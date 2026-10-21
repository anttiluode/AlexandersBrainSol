"""Source-locked, finite-time switching experiment. Python + NumPy only."""
import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path
import numpy as np
import ring

ROOT=Path(__file__).resolve().parent
METRICS=['write_accuracy','closed_replacement','closed_retention','idle_retention','read_accuracy','probe_damage','idle_damage']
SOURCE_FILES=['ring.py','experiment.py','protocols/switching.json','protocols/calibration.json','audit.py']


def decode(values, means):
    values=np.asarray(values)
    if not np.all(np.isfinite(values)):
        raise ValueError('sensor must be finite')
    thresholds=(np.asarray(means)[:-1]+np.asarray(means)[1:])/2
    if not np.all(np.diff(means)>0):
        raise ValueError('unordered calibration')
    return np.searchsorted(thresholds, values)-1


def verdict(s):
    checks=dict(replacement=s['write_accuracy']>=.95,
                closed_resistance=s['closed_replacement']<=.05 and s['closed_retention']>=.95,
                original_idle_retention=s['idle_retention']>=.95,
                local_read=s['read_accuracy']>=.95,
                probe_preservation=s['probe_damage']<=.01,
                idle_preservation=s['idle_damage']<=.01,
                refinement=bool(s['refinement_ok']))
    return dict(checks=checks, **{'pass':all(checks.values())})


def summarize(arms, refinement_ok):
    g=arms['gated']; c=arms['closed']; idle=arms['idle']
    valid=np.asarray(g['valid']); target=np.asarray(g['target'])
    written=valid & (np.asarray(g['final'])==target)
    # Failed/invalid writes remain in every denominator.
    read_correct=(np.asarray(g['reads'])==target[:,None]) & written[:,None]
    s=dict(write_accuracy=float(np.mean(written)),
           closed_replacement=float(np.mean(np.asarray(c['valid']) & (np.asarray(c['final'])==c['target']))),
           closed_retention=float(np.mean(np.asarray(c['valid']) & (np.asarray(c['final'])==c['old']))),
           idle_retention=float(np.mean(np.asarray(idle['valid']) & (np.asarray(idle['final'])==idle['old']))),
           read_accuracy=float(np.mean(read_correct)),
           probe_damage=float(np.mean(g['probe_changed'])),
           idle_damage=float(np.mean(g['idle_changed'])),
           refinement_ok=bool(refinement_ok))
    return s


def rotor_label(theta):
    phase=np.angle(np.exp(1j*theta))
    return np.clip(np.rint(phase/(2*np.pi/3)).astype(int),-1,1)


def rotor_evolve(theta, barrier, force, target, temperature, duration, dt, rng):
    theta=np.asarray(theta,dtype=float).copy()
    for _ in range(round(duration/dt)):
        drift=-3*barrier*np.sin(3*theta)
        if target is not None:
            drift += force*np.sin(target-theta)
        theta += dt*drift
        if temperature:
            theta += np.sqrt(2*temperature*dt)*rng.normal(size=theta.shape)
    return theta


def coarsen_noise(noise):
    if len(noise)%2:
        raise ValueError('even number of fine increments required')
    return noise[::2]+noise[1::2]


def hashes():
    return {f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in SOURCE_FILES}


def git_head():
    return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()


def require_full_lock(mode, lock):
    if mode!='full' or not lock or git_head()!=lock:
        raise ValueError('full run requires exact source lock HEAD')
    dirty=subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=ROOT,text=True)
    if dirty:
        raise ValueError('source lock requires clean tracked checkout')
    for path,digest in hashes().items():
        data=subprocess.check_output(['git','show',lock+':'+path],cwd=ROOT)
        if hashlib.sha256(data).hexdigest()!=digest:
            raise ValueError('current bytes differ from source lock: '+path)
    calibration=json.loads((ROOT/'protocols/calibration.json').read_text())
    for path,digest in calibration['source_hashes'].items():
        if hashes()[path]!=digest:raise ValueError('stale calibration: '+path)


def steps(p):
    return [(p['write_time'],True,True),(p['close_time'],False,True),
            (p['release_time'],False,False),(p['wait_time'],False,False)]


def controls(p, targets, arm, opened, biased):
    mu=np.ones(p['sites'])
    if opened and arm in ('gated','gate_only'):
        mu[:p['gate_sites']]=p['gate_mu']
    a=2*np.pi*targets[:,None]/p['sites'] if biased and arm in ('gated','closed') else 0.
    return mu,a


def write_ring(z,targets,arm,p,rng):
    for duration,opened,biased in steps(p):
        mu,a=controls(p,targets,arm,opened,biased)
        z=ring.evolve(z,mu,a,p['temperature'],duration,p['dt'],p['dx'],rng)
    return z


def read_ring(z,p,rng,sensor_rng,means,probe=True,count=None):
    original,valid=ring.winding(z)
    monitor=dict(reference=original,changed=~valid,minimum_amplitude=np.min(np.abs(z),axis=1))
    a=np.zeros(p['sites']);a[p['sensor_bond']]=p['read_phase'] if probe else 0
    readings=[];analog=[]
    for _ in range(p['read_count'] if count is None else count):
        samples=[]
        for _ in range(p['samples_per_read']):
            z=ring.evolve(z,np.ones(p['sites']),a,p['temperature'],p['read_time']/p['samples_per_read'],p['dt'],p['dx'],rng,monitor)
            samples.append(ring.current(z,p['sensor_bond'],p['dx'],a[p['sensor_bond']]))
        x=np.mean(samples,axis=0)+sensor_rng.normal(0,p['sensor_noise'],len(z))
        analog.append(x);readings.append(decode(x,means))
    return z,np.asarray(readings).T,np.asarray(analog).T,monitor


def initial(old,p,rng):
    z=ring.initial_state(old,p['sites'],p['dx'])
    # Global phase is unknown to reader/controller and shared across paired arms.
    return z*np.exp(1j*rng.uniform(-np.pi,np.pi,len(old)))[:,None]


def calibrate(p):
    labels=np.repeat([-1,0,1],p['calibration_replicas'])
    rng=np.random.default_rng(p['calibration_seed'])
    z=initial(labels,p,rng)
    z=ring.evolve(z,np.ones(p['sites']),0,p['temperature'],p['wait_time'],p['dt'],p['dx'],rng)
    _,_,analog,_=read_ring(z,p,rng,np.random.default_rng(p['calibration_seed']+1),[-.2,0,.2],count=1)
    return dict(seed=p['calibration_seed'],labels=labels.tolist(),values=analog[:,0].tolist(),
                means=[float(np.mean(analog[labels==n,0])) for n in [-1,0,1]],
                source_hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['ring.py','experiment.py','protocols/switching.json']})


def ordinary(old,target,p,seed):
    result={}
    for arm in ['gated','closed','gate_only','idle']:
        rng=np.random.default_rng(seed)
        theta=2*np.pi*old/3
        for duration,opened,biased in steps(p):
            barrier=p['rotor_open_barrier'] if opened and arm in ('gated','gate_only') else p['rotor_barrier']
            cue=2*np.pi*target/3 if biased and arm in ('gated','closed') else None
            theta=rotor_evolve(theta,barrier,p['rotor_force'],cue,p['temperature'],duration,p['dt'],rng)
        final=rotor_label(theta)
        readings=[];changed=np.zeros(len(theta),bool)
        for _ in range(p['read_count']):
            # A fixed weak sensor potential supplies target-independent backaction.
            for _ in range(round(p['read_time']/p['dt'])):
                theta += p['dt']*(-3*p['rotor_barrier']*np.sin(3*theta)-p['read_phase']*np.sin(theta))
                theta += np.sqrt(2*p['temperature']*p['dt'])*rng.normal(size=theta.shape)
                changed |= rotor_label(theta)!=final
            noisy=theta+rng.normal(0,p['sensor_noise'],len(theta))
            readings.append(rotor_label(noisy))
        result[arm]=dict(final=final.tolist(),replacement=float(np.mean(final==target)),
                         reads=np.asarray(readings).T.tolist(),changed=changed.tolist())
    return result


def refinement(p):
    """Coupled Brownian dt/dt2, all transitions, all write phases + repeated read."""
    old=np.array([-1,-1,0,0,1,1]);target=np.array([0,1,-1,1,-1,0])
    max_field=0.;max_current=0.;logical_equal=True
    rng=np.random.default_rng(p['refinement_seed'])
    phase_noise=np.random.default_rng(p['refinement_seed']+1)
    checks=[]
    for arm in ['gated','closed','gate_only','idle']:
        coarse=initial(old,p,rng);fine=coarse.copy()
        schedule=[(d,*controls(p,target,arm,o,b)) for d,o,b in steps(p)]
        local_a=np.zeros(p['sites']);local_a[p['sensor_bond']]=p['read_phase']
        schedule += [(p['read_time'],np.ones(p['sites']),local_a)]*p['read_count']
        for phase,(duration,mu,a) in enumerate(schedule):
            n=round(duration/(p['dt']/2))
            dw=np.sqrt(p['temperature']*p['dt']/p['dx'])*(phase_noise.normal(size=(n,len(old),p['sites']))+1j*phase_noise.normal(size=(n,len(old),p['sites'])))
            fine=ring.evolve(fine,mu,a,p['temperature'],duration,p['dt']/2,p['dx'],rng,increments=dw)
            coarse=ring.evolve(coarse,mu,a,p['temperature'],duration,p['dt'],p['dx'],rng,increments=coarsen_noise(dw))
            err=float(np.max(np.abs(coarse-fine)));cur=float(np.max(np.abs(ring.current(coarse,p['sensor_bond'],p['dx'])-ring.current(fine,p['sensor_bond'],p['dx']))))
            max_field=max(max_field,err);max_current=max(max_current,cur)
            # Winding is deliberately invalid while gate open; compare closed phases.
            if phase>=1:
                wc,vc=ring.winding(coarse);wf,vf=ring.winding(fine)
                logical_equal &= bool(np.array_equal(wc,wf) and np.array_equal(vc,vf))
            checks.append(dict(arm=arm,phase=phase,field_error=err,current_error=cur))
    return dict(max_field_error=max_field,max_current_error=max_current,logical_equal=logical_equal,
                **{'pass':max_field<=p['refinement_field_tolerance'] and max_current<=p['refinement_current_tolerance'] and logical_equal},checks=checks)


def run_seed(seed,p,means):
    pairs=np.array([(a,b) for a in [-1,0,1] for b in [-1,0,1] if a!=b])
    old=np.tile(pairs[:,0],p['replicas']);target=np.tile(pairs[:,1],p['replicas'])
    z=initial(old,p,np.random.default_rng(seed))
    arms={}
    for arm in ['gated','closed','gate_only','idle']:
        written=write_ring(z,target,arm,p,np.random.default_rng(seed+100000))
        final,valid=ring.winding(written)
        probed,reads,analog,monitor=read_ring(written,p,np.random.default_rng(seed+200000),np.random.default_rng(seed+300000),means)
        idle,_,_,idle_monitor=read_ring(written,p,np.random.default_rng(seed+200000),np.random.default_rng(seed+300000),means,probe=False)
        arms[arm]=dict(old=old.tolist(),target=target.tolist(),final=final.tolist(),valid=valid.tolist(),
                       reads=reads.tolist(),sensor_values=analog.tolist(),probe_changed=monitor['changed'].tolist(),
                       idle_changed=idle_monitor['changed'].tolist(),min_probe_amplitude=monitor['minimum_amplitude'].tolist(),
                       min_idle_amplitude=idle_monitor['minimum_amplitude'].tolist(),
                       written_real=written.real.tolist(),written_imag=written.imag.tolist(),
                       probed_real=probed.real.tolist(),probed_imag=probed.imag.tolist(),
                       idle_real=idle.real.tolist(),idle_imag=idle.imag.tolist())
    return dict(seed=seed,arms=arms,ordinary=ordinary(old,target,p,seed+400000),
                summary={k:v for k,v in summarize(arms,True).items() if k!='refinement_ok'},
                controls={a:dict(retention=float(np.mean(np.asarray(d['valid']) & (np.asarray(d['final'])==d['old']))),invalid=float(np.mean(~np.asarray(d['valid'])))) for a,d in arms.items()})


def json_ready(x):
    if isinstance(x,np.generic):return x.item()
    raise TypeError(type(x).__name__)


def save_new(path,data):
    with Path(path).open('x') as f:
        json.dump(data,f,indent=2,default=json_ready,allow_nan=False)
        f.write('\n')


def execute_seeds(seeds,runner,checkpoint_dir):
    rows=[]
    try:
        for seed in seeds:
            row=runner(seed)
            save_new(Path(checkpoint_dir)/f'seed-{seed}.json',row)
            rows.append(row)
            print(seed,row.get('summary',{}),flush=True)
    except BaseException as error:
        save_new(Path(checkpoint_dir)/'aborted.json',dict(completed_seeds=[r['seed'] for r in rows],error=type(error).__name__,message=str(error)))
        raise
    return rows


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['calibrate','development','full'])
    parser.add_argument('--lock');parser.add_argument('--output',required=True)
    args=parser.parse_args()
    p=json.loads((ROOT/'protocols/switching.json').read_text())
    if args.mode=='calibrate':
        save_new(args.output,calibrate(p));return
    if args.mode=='full':require_full_lock(args.mode,args.lock)
    before=hashes();head=git_head()
    output=Path(args.output)
    if output.exists():raise FileExistsError(output)
    checkpoints=output.with_suffix('.partial');checkpoints.mkdir(exist_ok=False)
    save_new(checkpoints/'started.json',dict(mode=args.mode,source_commit=head,hashes=before,protocol=p))
    means=json.loads((ROOT/'protocols/calibration.json').read_text())['means']
    ref=refinement(p)
    save_new(checkpoints/'refinement.json',ref)
    seeds=p['full_seeds'] if args.mode=='full' else p['development_seeds']
    rows=execute_seeds(seeds,lambda seed:run_seed(seed,p,means),checkpoints)
    summary={k:float(np.mean([r['summary'][k] for r in rows])) for k in METRICS}
    summary['refinement_ok']=bool(ref['pass'])
    if hashes()!=before or git_head()!=head:
        raise ValueError('source changed during run')
    receipt=dict(mode=args.mode,source_commit=head,hashes=before,protocol=p,calibration_means=means,
                 runtime=dict(python=platform.python_version(),numpy=np.__version__),
                 refinement=ref,seeds=seeds,rows=rows,summary=summary,verdict=verdict(summary))
    save_new(args.output,receipt)
    save_new(checkpoints/'completed.json',dict(receipt_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),seeds=seeds))
    print('verdict',receipt['verdict'],flush=True)

if __name__=='__main__':main()
