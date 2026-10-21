"""Small addressed array. Values and cue ports are supplied, not learned."""
import argparse,gzip,hashlib,itertools,json,platform,subprocess
from pathlib import Path
from functools import partial
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import ring
import experiment as ex

ROOT=Path(__file__).resolve().parent
ARMS=['trace','snap','oracle','shuffled','all_open','closed']
SOURCE_FILES=['addressed_updates.py','addressed_audit.py','protocols/addressed_updates.json',
              'ring.py','experiment.py','protocols/switching.json','protocols/calibration.json']
METRICS=['routing','writes','bystander_survival','whole_array','voted_read','read_survival']


def requests():
    old=np.asarray(list(itertools.permutations([-1,0,1])))
    addresses=np.asarray([np.roll([0,1,2],h%3).tolist()+[np.roll([0,1,2],h%3)[0]] for h in range(6)])
    values=np.zeros((6,4),int);expected=np.zeros((6,4,3),int);state=old.copy()
    for e in range(4):
        a=addresses[:,e];value=(state[np.arange(6),a]+2)%3-1
        values[:,e]=value;state[np.arange(6),a]=value;expected[:,e]=state
    return old,addresses,values,expected


def select(state,cue,delay,decay):
    m=np.asarray(state,dtype=float).copy()
    for sample in np.moveaxis(cue,1,0):m=decay*m+(1-decay)*np.maximum(sample,0)
    snapped=np.argmax(m,axis=1)
    for sample in np.moveaxis(delay,1,0):m=decay*m+(1-decay)*np.maximum(sample,0)
    return m,np.argmax(m,axis=1),snapped


def gate_mask(arm,trace,snap,address):
    if arm=='all_open':return np.ones((len(address),3),bool)
    if arm=='closed':return np.zeros((len(address),3),bool)
    choice={'trace':trace,'snap':snap,'oracle':address,'shuffled':(address+1)%3}[arm]
    return np.arange(3)[None,:]==choice[:,None]


def operational(s,refined,p=None):
    p=p or json.loads((ROOT/'protocols/addressed_updates.json').read_text())
    checks={k:s[k]>=threshold for k,threshold in p['operational'].items()}
    checks['read_survival']=s['read_survival']>=.99
    checks['numerical']=bool(refined)
    return dict(checks=checks,**{'pass':all(checks.values())})


def symbol_vote(reads):
    counts=np.stack([(reads==n).sum(axis=-1) for n in [-1,0,1]],axis=-1)
    return np.where(counts.max(axis=-1)>=3,counts.argmax(axis=-1)-1,2)


def controls(opened,value,p,open_phase,biased):
    mu=np.ones((len(value),3,p['sites']))
    if open_phase:mu[:,:,:p['gate_sites']]=np.where(opened[:,:,None],p['gate_mu'],1.)
    a=np.repeat(value,3)[:,None]*2*np.pi/p['sites'] if biased else 0.
    return mu.reshape(-1,p['sites']),a


def record(z):
    return dict(real=z.real.tolist(),imag=z.imag.tolist())


def monitor(z):
    w,valid=ring.winding(z)
    return dict(reference=w,changed=~valid,minimum_amplitude=np.min(np.abs(z),axis=1))


def oracle_labels(z,h):
    w,v=ring.winding(z)
    return w.reshape(h,3),v.reshape(h,3)


def event_noise(seed,p,h):
    rng=np.random.default_rng(seed+20000)
    return [(rng.normal(0,p['cue_noise'],size=(h,p['cue_samples'],3)),
             rng.normal(0,p['delay_noise'],size=(h,p['delay_samples'],3))) for _ in range(p['events'])]


def summaries(events):
    return {k:float(np.mean([np.mean(row[k]) for row in events])) for k in METRICS}


def ordinary_event(theta,opened,value,p,ap,rng,address):
    reference=ex.rotor_label(theta).copy();bad=np.zeros(theta.shape,bool)
    for duration,open_phase,biased in ex.steps(p):
        barrier=np.where(opened,p['rotor_open_barrier'],p['rotor_barrier']) if open_phase else p['rotor_barrier']
        cue=2*np.pi*value[:,None]/3 if biased else None
        for _ in range(round(duration/p['dt'])):
            drift=-3*barrier*np.sin(3*theta)
            if cue is not None:drift+=p['rotor_force']*np.sin(cue-theta)
            theta+=p['dt']*drift+np.sqrt(2*p['temperature']*p['dt'])*rng.normal(size=theta.shape)
            bad|=ex.rotor_label(theta)!=reference
    reads=[];stored=ex.rotor_label(theta).copy();read_bad=np.zeros(theta.shape,bool)
    for _ in range(ap['queries']):
        for _ in range(round(p['read_time']/p['dt'])):
            theta+=p['dt']*(-3*p['rotor_barrier']*np.sin(3*theta)-p['read_phase']*np.sin(theta))+np.sqrt(2*p['temperature']*p['dt'])*rng.normal(size=theta.shape)
            read_bad|=ex.rotor_label(theta)!=stored
        reads.append(ex.rotor_label(theta+rng.normal(0,p['sensor_noise'],size=theta.shape)))
    return theta,ex.rotor_label(theta),bad,read_bad,symbol_vote(np.stack(reads,axis=-1))


def run_seed(seed,ap,p,means):
    old,addresses,values,expected=requests();h=len(old)
    cue_noise=event_noise(seed,ap,h)
    # Initial phase and all process/sensor streams are paired across arms.
    initial=ex.initial(old.ravel(),p,np.random.default_rng(seed+10000))
    arms={}
    for arm in ARMS:
        z=initial.copy();theta=2*np.pi*old/3
        rng=np.random.default_rng(seed+30000);sensor=np.random.default_rng(seed+40000)
        rotor_rng=np.random.default_rng(seed+50000);events=[]
        for e in range(ap['events']):
            address=addresses[:,e];value=values[:,e];goal=expected[:,e]
            cue,delay=(a.copy() for a in cue_noise[e]);cue[np.arange(h),:,address]+=1.
            # Explicit cue-onset reset: no hidden analog state enters the snapped latch.
            material,trace,snap=select(np.zeros((h,3)),cue,delay,ap['trace_decay'])
            opened=gate_mask(arm,trace,snap,address)
            before,pre_valid=oracle_labels(z,h);damage=monitor(z)
            bystander=np.arange(3)[None,:]!=address[:,None]
            for duration,open_phase,biased in ex.steps(p):
                mu,a=controls(opened,value,p,open_phase,biased)
                z=ring.evolve(z,mu,a,p['temperature'],duration,p['dt'],p['dx'],rng,damage)
            after,valid=oracle_labels(z,h)
            written=record(z)
            z,reads,analog,read_damage=ex.read_ring(z,p,rng,sensor,means,count=ap['queries'])
            final,valid_final=oracle_labels(z,h);vote=symbol_vote(reads).reshape(h,3)
            bad=(damage['changed']|read_damage['changed']).reshape(h,3)
            rd=read_damage['changed'].reshape(h,3)
            theta,rfinal,rbad,rrbad,rvote=ordinary_event(theta,opened,value,p,ap,rotor_rng,address)
            rows=np.arange(h)
            events.append(dict(event=e,address=address.tolist(),command=value.tolist(),goal=goal.tolist(),
                cue=cue.tolist(),delay=delay.tolist(),trace=material.tolist(),trace_address=trace.tolist(),snap_address=snap.tolist(),opened=opened.tolist(),
                before=before.tolist(),before_valid=pre_valid.tolist(),after_write=after.tolist(),after_write_valid=valid.tolist(),
                final=final.tolist(),valid=valid_final.tolist(),written=written,field=record(z),sensor_values=analog.tolist(),reads=reads.tolist(),vote=vote.tolist(),
                bystander_bad=bad[bystander].reshape(h,2).tolist(),read_bad=rd.tolist(),
                routing=((opened.sum(axis=1)==1)&opened[rows,address]).tolist(),
                writes=(valid_final[rows,address]&(final[rows,address]==value)).tolist(),
                bystander_survival=(~bad[bystander]).reshape(h,2).tolist(),
                whole_array=(np.all(valid_final,axis=1)&np.all(final==goal,axis=1)).tolist(),
                voted_read=((vote==goal)&valid_final).tolist(),read_survival=(~rd).tolist(),
                stored_read=((vote==final)&valid_final).tolist(),
                ordinary=dict(theta=theta.tolist(),final=rfinal.tolist(),vote=rvote.tolist(),bystander_survival=(~(rbad|rrbad)[bystander]).reshape(h,2).tolist(),
                  writes=(rfinal[rows,address]==value).tolist(),whole_array=np.all(rfinal==goal,axis=1).tolist(),voted_read=(rvote==goal).tolist(),read_survival=(~rrbad).tolist())))
        arms[arm]=dict(events=events,summary=summaries(events))
    return dict(seed=seed,initial=old.tolist(),arms=arms)


def refinement(ap,p):
    old,addresses,values,_=requests();h=1
    noises=event_noise(ap['refinement_seed'],ap,6)
    rng=np.random.default_rng(ap['refinement_seed']+1)
    dw_rng=np.random.default_rng(ap['refinement_seed']+2)
    max_field=max_current=0.;same=True;checks=[]
    for arm in ARMS:
        coarse=ex.initial(old[:1].ravel(),p,rng);fine=coarse.copy()
        for e in range(ap['events']):
            address=addresses[:1,e];value=values[:1,e]
            cue=noises[e][0][:1].copy();cue[np.arange(h),:,address]+=1
            _,trace,snap=select(np.zeros((h,3)),cue,noises[e][1][:1],ap['trace_decay'])
            opened=gate_mask(arm,trace,snap,address)
            schedule=[(duration,*controls(opened,value,p,o,b),i!=0) for i,(duration,o,b) in enumerate(ex.steps(p))]
            read_a=np.zeros(p['sites']);read_a[p['sensor_bond']]=p['read_phase']
            schedule += [(p['read_time'],np.ones(p['sites']),read_a,True)]*ap['queries']
            for phase,(duration,mu,a,closed) in enumerate(schedule):
                n=round(2*duration/p['dt']);shape=(n,*coarse.shape)
                dw=np.sqrt(p['temperature']*p['dt']/p['dx'])*(dw_rng.normal(size=shape)+1j*dw_rng.normal(size=shape))
                fine=ring.evolve(fine,mu,a,p['temperature'],duration,p['dt']/2,p['dx'],rng,increments=dw)
                coarse=ring.evolve(coarse,mu,a,p['temperature'],duration,p['dt'],p['dx'],rng,increments=ex.coarsen_noise(dw))
                fe=float(np.max(np.abs(fine-coarse)))
                cur=float(np.max(np.abs(ring.current(fine,p['sensor_bond'],p['dx'])-ring.current(coarse,p['sensor_bond'],p['dx']))))
                max_field=max(max_field,fe);max_current=max(max_current,cur)
                if closed:
                    wc,vc=ring.winding(coarse);wf,vf=ring.winding(fine)
                    same &= bool(np.array_equal(wc,wf) and np.array_equal(vc,vf))
                checks.append(dict(arm=arm,event=e,phase=phase,field_error=fe,current_error=cur))
    return dict(max_field_error=max_field,max_current_error=max_current,logical_equal=same,
                **{'pass':same and max_field<=ap['field_tolerance'] and max_current<=ap['current_tolerance']},checks=checks)


def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCE_FILES}

def source_check(lock):
    if ex.git_head()!=lock:raise ValueError('exact source HEAD required')
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=ROOT,text=True):raise ValueError('dirty source')
    for name,sha in hashes().items():
        data=subprocess.check_output(['git','show',lock+':'+name],cwd=ROOT)
        if hashlib.sha256(data).hexdigest()!=sha:raise ValueError('source differs: '+name)
    calibration=json.loads((ROOT/'protocols/calibration.json').read_text())
    for name,sha in calibration['source_hashes'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=sha:raise ValueError('calibration differs')


def save_gzip(path,data):
    raw=(json.dumps(data,default=ex.json_ready,allow_nan=False,separators=(',',':'))+'\n').encode()
    compressed=gzip.compress(raw,mtime=0)
    with Path(path).open('xb') as f:f.write(compressed)
    return dict(file=Path(path).name,sha256=hashlib.sha256(compressed).hexdigest(),raw_sha256=hashlib.sha256(raw).hexdigest(),raw_bytes=len(raw))


def run_saved(seed,ap,p,means,directory):
    row=run_seed(seed,ap,p,means)
    metadata=save_gzip(Path(directory)/f'seed-{seed}.json.gz',row)
    print(seed,{a:row['arms'][a]['summary'] for a in ['trace','snap','oracle']},flush=True)
    return dict(seed=seed,receipt=metadata,summaries={a:d['summary'] for a,d in row['arms'].items()})


def aggregate(rows,ref,ap):
    summaries={a:{k:float(np.mean([r['summaries'][a][k] for r in rows])) for k in METRICS} for a in ARMS}
    gains=[r['summaries']['trace']['whole_array']-r['summaries']['snap']['whole_array'] for r in rows]
    advantage=dict(whole_array_gain=float(np.mean(gains)),positive_seed_fraction=float(np.mean(np.asarray(gains)>0)))
    advantage['pass']=(advantage['whole_array_gain']>=ap['analog_benefit']['whole_array_gain'] and advantage['positive_seed_fraction']>=ap['analog_benefit']['positive_seed_fraction'] and summaries['trace']['bystander_survival']>=summaries['snap']['bystander_survival'] and summaries['trace']['voted_read']>=summaries['snap']['voted_read'])
    return dict(summaries=summaries,operational={a:operational(d,ref['pass'],ap) for a,d in summaries.items()},analog_benefit=advantage)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['development','full']);parser.add_argument('--lock');parser.add_argument('--output-dir',required=True);args=parser.parse_args()
    ap=json.loads((ROOT/'protocols/addressed_updates.json').read_text());p=json.loads((ROOT/'protocols/switching.json').read_text());means=json.loads((ROOT/'protocols/calibration.json').read_text())['means']
    if args.mode=='full':source_check(args.lock)
    before=hashes();head=ex.git_head();directory=Path(args.output_dir);directory.mkdir(exist_ok=False,parents=True)
    header=dict(mode=args.mode,source_commit=head,hashes=before,address_protocol=ap,cell_protocol=p,calibration_means=means,runtime=dict(python=platform.python_version(),numpy=np.__version__))
    ex.save_new(directory/'started.json',header)
    try:
        ref=refinement(ap,p);ex.save_new(directory/'refinement.json',ref)
        if args.mode=='full' and not ref['pass']:raise ValueError('refinement failed before fresh seeds')
        seeds=ap['full_seeds'] if args.mode=='full' else ap['development_seeds']
        with ProcessPoolExecutor(max_workers=ap['workers']) as pool:rows=list(pool.map(partial(run_saved,ap=ap,p=p,means=means,directory=str(directory)),seeds))
        if before!=hashes() or head!=ex.git_head():raise ValueError('source changed')
        manifest=dict(**header,seeds=seeds,rows=rows,refinement=ref,result=aggregate(rows,ref,ap))
        ex.save_new(directory/'manifest.json',manifest)
        print(manifest['result'],flush=True)
    except BaseException as error:
        ex.save_new(directory/'aborted.json',dict(error=type(error).__name__,message=str(error),completed_files=[q.name for q in directory.glob('seed-*.json.gz')]))
        raise

if __name__=='__main__':main()
