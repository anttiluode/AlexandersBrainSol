"""Descriptive report. Five-query pooling is secondary and cannot rescue a gate."""
import argparse,gzip,json
from pathlib import Path
import numpy as np


def load(path):
    path=Path(path)
    data=gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes()
    return json.loads(data)


def vote_five(labels):
    labels=np.asarray(labels)
    if labels.ndim!=2 or labels.shape[1]%5 or not np.all(np.isin(labels,[-1,0,1])):
        raise ValueError('five-query control requires valid three-state symbols')
    grouped=labels.reshape(len(labels),-1,5)
    counts=np.stack([(grouped==n).sum(axis=-1) for n in [-1,0,1]],axis=-1)
    return np.where(counts.max(axis=-1)>=3,counts.argmax(axis=-1)-1,2)


def analyze(receipt):
    means=np.asarray(receipt['calibration_means']);thresholds=(means[1:]+means[:-1])/2
    result={}
    for arm in ['gated','closed','gate_only','idle']:
        metrics=[]
        for row in receipt['rows']:
            d=row['arms'][arm];target=np.asarray(d['target']);old=np.asarray(d['old'])
            valid=np.asarray(d['valid']);final=np.asarray(d['final']);written=valid & (final==target)
            sensor=np.asarray(d['sensor_values']);reads=np.asarray(d['reads'])
            pooled=np.searchsorted(thresholds,sensor.reshape(len(sensor),-1,5).mean(axis=2))-1
            voted=vote_five(reads)
            changed=np.asarray(d['probe_changed']);no_probe=np.asarray(d['idle_changed'])
            metrics.append(dict(replacement=float(np.mean(written)),old_retention=float(np.mean(valid & (final==old))),
                                invalid=float(np.mean(~valid)),
                                read_accuracy=float(np.mean((reads==target[:,None]) & written[:,None])),
                                state_read_accuracy=float(np.mean((reads==final[:,None]) & valid[:,None])),
                                pooled_accuracy=float(np.mean((pooled==target[:,None]) & written[:,None])),
                                vote_accuracy=float(np.mean((voted==target[:,None]) & written[:,None])),
                                vote_coverage=float(np.mean(voted!=2)),
                                damage=float(np.mean(changed)),no_probe_damage=float(np.mean(no_probe)),
                                conditional_damage=float(np.mean(changed[written])) if np.any(written) else None,
                                workflow_success=float(np.mean(written & ~changed)),
                                histories=len(old),queries=reads.size))
        keys=metrics[0].keys()
        result[arm]={k:float(np.mean([m[k] for m in metrics if m[k] is not None])) if any(m[k] is not None for m in metrics) else None for k in keys}
        result[arm]['per_seed']=metrics
    ordinary={}
    for arm in result:
        rows=[r['ordinary'][arm] for r in receipt['rows']]
        ordinary[arm]=dict(replacement=float(np.mean([d['replacement'] for d in rows])),
                           damage=float(np.mean([np.mean(d['changed']) for d in rows])),
                           read_accuracy=float(np.mean([np.mean(np.asarray(d['reads'])==np.asarray(r['arms'][arm]['target'])[:,None]) for d,r in zip(rows,receipt['rows'])])))
    return dict(source_commit=receipt['source_commit'],mode=receipt['mode'],summary=receipt['summary'],
                verdict=receipt['verdict'],ring=result,ordinary=ordinary,
                refinement={k:v for k,v in receipt['refinement'].items() if k!='checks'},
                independent_units=len(receipt['rows']),histories=sum(len(r['arms']['gated']['old']) for r in receipt['rows']),
                queries=sum(np.asarray(r['arms']['gated']['reads']).size for r in receipt['rows']))


def markdown(r):
    lines=['# Switching-memory result','',f"Source: `{r['source_commit']}`; mode: **{r['mode']}**.",
           f"{r['independent_units']} independent noise-seed batches, {r['histories']} transition histories, {r['queries']} successive local queries.",'',
           '| Ring arm | Requested replacement | Old state retained | Reads requested label | Five-query analog average | Five-query symbol vote | Any monitored read damage |',
           '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for name,d in r['ring'].items():
        lines.append('| '+name+' | '+' | '.join(f'{100*d[k]:.2f}%' for k in ['replacement','old_retention','read_accuracy','pooled_accuracy','vote_accuracy','damage'])+' |')
    lines += ['',f"**Declared overall gate: {'PASS' if r['verdict']['pass'] else 'FAIL'}.**",
              'Checks: '+', '.join(k+'='+str(v) for k,v in r['verdict']['checks'].items())+'.','',
              'Read accuracy in this table means the requested label, with failed writes counted as errors. Closed and idle arms deliberately resist that request; their low requested-label scores are expected. The JSON report separately gives accuracy against the actual valid stored integer. Five-query pooling costs ten time units instead of two and reduces the output rate fivefold. It was identified during development and is a secondary diagnostic, not a replacement for the failed single-query criterion. The quantized control uses only five already-rounded three-state symbols (encodable in 2 bits each; the implementation stores integers); it requires a strict majority, counts abstentions as errors, and has no access to analog magnitudes. The analog average retains five floating scalar measurements. Both secondary controls use the same five queries and cannot rescue the primary gate. Temporal queries are correlated; they are not independent trials.',
              '', '| Ordinary three-well control | Requested replacement | Read correct | Monitored damage |', '| --- | ---: | ---: | ---: |']
    for name,d in r['ordinary'].items():lines.append(f"| {name} | {100*d['replacement']:.2f}% | {100*d['read_accuracy']:.2f}% | {100*d['damage']:.2f}% |")
    lines += ['', 'The ordinary control shows whether the basic gated-memory behavior is generic. Energy, microscopic noise and state dimensions are not matched; these percentages establish no efficiency or topology-specific advantage.', '',
              'Numerical refinement: '+json.dumps(r['refinement'],sort_keys=True)+'.', '',
              'Scope: prescribed 1D ring, three states, idealized local sensor, engineered write controller, fixed finite time and noise. No learning, grown network, physical mass or permanent protection is established.']
    return '\n'.join(lines)+'\n'


def main():
    p=argparse.ArgumentParser();p.add_argument('receipt');p.add_argument('--output',required=True);args=p.parse_args()
    r=analyze(load(args.receipt))
    with Path(args.output).open('x') as f:f.write(markdown(r))
    with Path(args.output).with_suffix('.json').open('x') as f:json.dump(r,f,indent=2)
    print(json.dumps({k:r[k] for k in ['summary','verdict','histories','queries']},indent=2))

if __name__=='__main__':main()
