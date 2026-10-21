"""Independent exact-source worktree replay, started before final manifest existed.

Adds no scientific dynamics. Uses the locked experiment and comparator, saves
independent checkpoints, then verifies each original complete compressed receipt.
"""
import gzip, hashlib, json, platform, subprocess, sys, time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
LOCKED=Path('/workspace/scratch/33f81f82f09d/alexander-addressed-locked')
ORIGINAL=Path('/workspace/scratch/33f81f82f09d/AlexandersBrainSol/results/addressed_updates/full')
OUTPUT=ORIGINAL.parent/'independent-replay'
sys.path.insert(0,str(LOCKED))
import numpy as np
import numba
import addressed_updates as au
import addressed_audit as aa
import experiment as ex
import audit

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def replay(seed,ap,p,means):
    row=au.run_seed(seed,ap,p,means)
    receipt=au.save_gzip(OUTPUT/f'seed-{seed}.json.gz',row)
    print('independent complete',seed,flush=True)
    return dict(seed=seed,receipt=receipt,summaries={a:d['summary'] for a,d in row['arms'].items()})

def leaves(x,counts):
    if isinstance(x,dict):
        for v in x.values():leaves(v,counts)
    elif isinstance(x,list):
        for v in x:leaves(v,counts)
    elif isinstance(x,float):counts['floating_leaves']+=1
    else:counts['exact_nonfloating_leaves']+=1

def main():
    started_path=ORIGINAL/'started.json';started_digest=digest(started_path)
    header=json.loads(started_path.read_text())
    if header['mode']!='full':raise ValueError('full original required')
    lock=header['source_commit'];au.source_check(lock)
    ap=header['address_protocol'];p=header['cell_protocol'];seeds=ap['full_seeds']
    aa.verify(dict(**header,seeds=seeds,rows=[dict(seed=s) for s in seeds]))
    audit.compare(p,json.loads((LOCKED/'protocols/switching.json').read_text()),0,0)
    runtime=dict(python=platform.python_version(),numpy=np.__version__,numba=numba.__version__,backend='array_backend')
    audit.compare(header['runtime'],runtime,0,0)
    rt,at=ap['audit_rtol'],ap['audit_atol'];stats=dict(floats=0,max_absolute_difference=0.)
    source_before=au.hashes()
    proof=dict(source_commit=lock,worktree=str(LOCKED),worktree_head=ex.git_head(),
      tracked_worktree_status=subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=LOCKED,text=True),
      source_hashes=source_before,wrapper_sha256=digest(__file__),original_started_sha256=started_digest,
      runtime=runtime,rtol=rt,atol=at,seeds=seeds)
    ex.save_new(OUTPUT/'started.json',proof)
    print('independent exact source verified; replaying original NumPy calibration',flush=True)
    calibration=json.loads((LOCKED/'protocols/calibration.json').read_text())
    audit.compare(calibration,ex.calibrate(p),rt,at,stats=stats)
    audit.compare(header['calibration_means'],calibration['means'],rt,at,stats=stats)
    ex.save_new(OUTPUT/'calibration-check.json',dict(pass_calibration=True,numerics=stats.copy()))
    print('calibration verified; replaying full-sequence sampled refinement',flush=True)
    ref=au.refinement(ap,p)
    audit.compare(json.loads((ORIGINAL/'refinement.json').read_text()),ref,rt,at,stats=stats)
    ex.save_new(OUTPUT/'refinement.json',ref)
    print('refinement verified',ref['pass'],'launching five full seeded histories',flush=True)
    entries={}
    with ProcessPoolExecutor(max_workers=ap['workers']) as pool:
        futures=[pool.submit(replay,s,ap,p,calibration['means']) for s in seeds]
        for future in as_completed(futures):
            row=future.result();entries[row['seed']]=row
    ex.save_new(OUTPUT/'replay-manifest.json',dict(**proof,rows=[entries[s] for s in seeds],refinement=ref))
    while not (ORIGINAL/'manifest.json').exists():
        if (ORIGINAL/'aborted.json').exists():raise ValueError('original full experiment aborted')
        print('independent histories complete; waiting for original final manifest',flush=True)
        time.sleep(5)
    manifest_path=ORIGINAL/'manifest.json';manifest_digest=digest(manifest_path)
    manifest=json.loads(manifest_path.read_text());aa.verify(manifest)
    for key in header:audit.compare(header[key],manifest[key],rt,at,stats=stats)
    audit.compare(manifest['refinement'],ref,rt,at,stats=stats)
    counts=dict(floating_leaves=0,exact_nonfloating_leaves=0)
    raw_receipts=[];rows=[]
    for entry in manifest['rows']:
        original=aa.load_seed(ORIGINAL,entry)
        independent=aa.load_seed(OUTPUT,entries[entry['seed']])
        audit.compare(original,independent,rt,at,stats=stats)
        leaves(original,counts)
        summaries={a:d['summary'] for a,d in independent['arms'].items()}
        audit.compare(entry['summaries'],summaries,rt,at,stats=stats)
        rows.append(dict(seed=entry['seed'],summaries=summaries))
        raw_receipts.append(dict(seed=entry['seed'],original=entry['receipt'],independent=entries[entry['seed']]['receipt']))
    audit.compare(manifest['result'],au.aggregate(rows,ref,ap),rt,at,stats=stats)
    au.source_check(lock)
    if source_before!=au.hashes() or digest(started_path)!=started_digest or digest(manifest_path)!=manifest_digest or digest(__file__)!=proof['wrapper_sha256']:
        raise ValueError('source, wrapper or original metadata changed during audit')
    result=dict(**proof,pass_audit=True,source_verified=True,original_manifest_sha256=manifest_digest,
      original_compressed_and_raw_digests_verified=True,full_histories_replayed=True,
      all_controller_field_read_ordinary_outputs_compared=True,all_summaries_and_verdicts_compared=True,
      calibration_replayed=True,refinement_replayed=True,numerics=stats,receipt_leaf_counts=counts,
      experiment_counts=dict(seed_batches=len(seeds),arms=len(au.ARMS),histories_per_arm=6,events_per_history=ap['events'],
      array_event_endpoints=len(seeds)*len(au.ARMS)*6*ap['events'],
      cell_event_endpoints=len(seeds)*len(au.ARMS)*6*ap['events']*3,
      bystander_exposures=len(seeds)*len(au.ARMS)*6*ap['events']*2,
      primary_queries=len(seeds)*len(au.ARMS)*6*ap['events']*3*ap['queries']),receipts=raw_receipts)
    ex.save_new(ORIGINAL.parent/'independent-audit.json',result)
    print('INDEPENDENT AUDIT PASS',stats,counts,flush=True)

if __name__=='__main__':main()
