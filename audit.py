"""Replay raw trajectories; write a new audit, never modify original receipts."""
import argparse
import gzip
from concurrent.futures import ProcessPoolExecutor
from functools import partial
import hashlib
import json
import subprocess
import numpy as np
import experiment as ex


def compare(saved, regenerated, rtol, atol, path='$', stats=None):
    if stats is None:stats={'floats':0,'max_absolute_difference':0.}
    if isinstance(saved,dict):
        if not isinstance(regenerated,dict) or saved.keys()!=regenerated.keys():
            raise AssertionError(path+': keys mismatch')
        for k in saved:compare(saved[k],regenerated[k],rtol,atol,path+'.'+k,stats)
    elif isinstance(saved,list):
        if not isinstance(regenerated,list) or len(saved)!=len(regenerated):
            raise AssertionError(path+': length mismatch')
        for i,(a,b) in enumerate(zip(saved,regenerated)):compare(a,b,rtol,atol,f'{path}[{i}]',stats)
    elif isinstance(saved,(float,np.floating)):
        if not isinstance(regenerated,(int,float,np.number)) or not np.isfinite(saved) or not np.isfinite(regenerated) or not np.isclose(saved,regenerated,rtol=rtol,atol=atol):
            raise AssertionError(path+': numeric mismatch')
        stats['floats']+=1
        stats['max_absolute_difference']=max(stats['max_absolute_difference'],abs(saved-regenerated))
    elif type(saved)!=type(regenerated) or saved!=regenerated:
        raise AssertionError(path+': exact mismatch')
    return stats


def verify_source(receipt):
    if receipt['hashes']!=ex.hashes():
        raise ValueError('current implementation differs from receipt source')
    for path,digest in receipt['hashes'].items():
        data=subprocess.check_output(['git','show',receipt['source_commit']+':'+path],cwd=ex.ROOT)
        if hashlib.sha256(data).hexdigest()!=digest:
            raise ValueError('receipt hash differs from exact source commit: '+path)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('receipt');parser.add_argument('--output',required=True)
    args=parser.parse_args()
    path=ex.Path(args.receipt)
    raw=path.read_bytes()
    receipt=json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)
    verify_source(receipt)
    p=receipt['protocol'];rtol=p['audit_rtol'];atol=p['audit_atol']
    compare(p,json.loads((ex.ROOT/'protocols/switching.json').read_text()),0,0)
    expected=p['full_seeds'] if receipt['mode']=='full' else p['development_seeds']
    if receipt['seeds']!=expected or [r['seed'] for r in receipt['rows']]!=expected:
        raise ValueError('missing, duplicated or unexpected seed rows')
    before=ex.hashes()
    calibration=ex.calibrate(p)
    stats=compare(json.loads((ex.ROOT/'protocols/calibration.json').read_text()),calibration,rtol,atol)
    compare(receipt['calibration_means'],calibration['means'],rtol,atol,stats=stats)
    ref=ex.refinement(p)
    compare(receipt['refinement'],ref,rtol,atol,stats=stats)
    with ProcessPoolExecutor(max_workers=p['workers']) as pool:
        regenerated_rows=pool.map(partial(ex.run_seed,p=p,means=calibration['means']),expected)
        for saved,regenerated in zip(receipt['rows'],regenerated_rows):
            compare(saved,regenerated,rtol,atol,stats=stats)
            print('replayed',saved['seed'],flush=True)
    summary={k:float(np.mean([r['summary'][k] for r in receipt['rows']])) for k in ex.METRICS}
    summary['refinement_ok']=bool(ref['pass'])
    compare(receipt['summary'],summary,rtol,atol,stats=stats)
    compare(receipt['verdict'],ex.verdict(summary),rtol,atol,stats=stats)
    if before!=ex.hashes():raise ValueError('source changed during replay')
    report=dict(receipt_sha256=hashlib.sha256(ex.Path(args.receipt).read_bytes()).hexdigest(),
                source_commit=receipt['source_commit'],source_verified=True,seeds=expected,
                rtol=rtol,atol=atol,numerics=stats,pass_audit=True)
    ex.save_new(args.output,report)
    print(report,flush=True)

if __name__=='__main__':main()
