"""Separate full replay of complete compressed addressed-array histories."""
import argparse,gzip,hashlib,json,subprocess
from pathlib import Path
from functools import partial
from concurrent.futures import ProcessPoolExecutor
import addressed_updates as au
import audit
import experiment as ex


def load_seed(directory,row):
    path=Path(directory)/row['receipt']['file'];data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=row['receipt']['sha256']:raise ValueError('compressed receipt hash mismatch')
    raw=gzip.decompress(data)
    if hashlib.sha256(raw).hexdigest()!=row['receipt']['raw_sha256'] or len(raw)!=row['receipt']['raw_bytes']:raise ValueError('raw receipt hash mismatch')
    return json.loads(raw)


def verify(manifest):
    if manifest['hashes']!=au.hashes():raise ValueError('current implementation differs')
    for name,sha in manifest['hashes'].items():
        data=subprocess.check_output(['git','show',manifest['source_commit']+':'+name],cwd=au.ROOT)
        if hashlib.sha256(data).hexdigest()!=sha:raise ValueError('committed source differs')
    p=json.loads((au.ROOT/'protocols/addressed_updates.json').read_text())
    if p!=manifest['address_protocol']:raise ValueError('protocol differs')
    seeds=p['full_seeds'] if manifest['mode']=='full' else p['development_seeds']
    if manifest['seeds']!=seeds or [r['seed'] for r in manifest['rows']]!=seeds:raise ValueError('seed rows differ')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('directory');parser.add_argument('--output',required=True);args=parser.parse_args()
    directory=Path(args.directory);data=(directory/'manifest.json').read_bytes();manifest=json.loads(data)
    verify(manifest);before=au.hashes();p=manifest['cell_protocol'];ap=manifest['address_protocol']
    rt,at=ap['audit_rtol'],ap['audit_atol'];stats={'floats':0,'max_absolute_difference':0.}
    audit.compare(p,json.loads((au.ROOT/'protocols/switching.json').read_text()),0,0)
    calibration=json.loads((au.ROOT/'protocols/calibration.json').read_text())
    audit.compare(manifest['calibration_means'],calibration['means'],rt,at,stats=stats)
    # Reproduce the source-bound original sensor calibration as well.
    audit.compare(calibration,ex.calibrate(p),rt,at,stats=stats)
    ref=au.refinement(ap,p);audit.compare(manifest['refinement'],ref,rt,at,stats=stats)
    with ProcessPoolExecutor(max_workers=ap['workers']) as pool:
        regenerated=pool.map(partial(au.run_seed,ap=ap,p=p,means=calibration['means']),manifest['seeds'])
        rows=[]
        for entry,new in zip(manifest['rows'],regenerated):
            original=load_seed(directory,entry)
            audit.compare(original,new,rt,at,stats=stats)
            summaries={a:d['summary'] for a,d in new['arms'].items()}
            audit.compare(entry['summaries'],summaries,rt,at,stats=stats)
            rows.append(dict(seed=new['seed'],summaries=summaries))
            print('replayed',new['seed'],flush=True)
    audit.compare(manifest['result'],au.aggregate(rows,ref,ap),rt,at,stats=stats)
    if before!=au.hashes():raise ValueError('source changed during audit')
    result=dict(pass_audit=True,source_commit=manifest['source_commit'],source_verified=True,manifest_sha256=hashlib.sha256(data).hexdigest(),seeds=manifest['seeds'],rtol=rt,atol=at,numerics=stats,full_histories_replayed=True,calibration_replayed=True,refinement_replayed=True)
    ex.save_new(args.output,result);print(result,flush=True)

if __name__=='__main__':main()
