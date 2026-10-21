"""Recover a truncated aggregate from unchanged, complete seed checkpoints.

No simulation or seed selection occurs here. Require exact equality with the
SHA256 recorded by the original producer before accepting recovered bytes.
Original truncated bytes are preserved with a distinct name and gzip archive.
"""
import gzip,hashlib,json,shutil
from pathlib import Path
import numpy as np

root=Path(__file__).resolve().parent
raw_path=root/'full.json'
raw=raw_path.read_bytes()
marker=b'\n  "rows": ['
position=raw.index(marker)
receipt=json.loads(raw[:position]+b'\n  "rows": []\n}')
checkpoints=root/'full.partial'
receipt['rows']=[json.loads((checkpoints/f'seed-{s}.json').read_text()) for s in receipt['seeds']]
metrics=['write_accuracy','closed_replacement','closed_retention','idle_retention','read_accuracy','probe_damage','idle_damage']
summary={k:float(np.mean([r['summary'][k] for r in receipt['rows']])) for k in metrics}
summary['refinement_ok']=bool(receipt['refinement']['pass'])
checks=dict(replacement=summary['write_accuracy']>=.95,
            closed_resistance=summary['closed_replacement']<=.05 and summary['closed_retention']>=.95,
            original_idle_retention=summary['idle_retention']>=.95,
            local_read=summary['read_accuracy']>=.95,
            probe_preservation=summary['probe_damage']<=.01,
            idle_preservation=summary['idle_damage']<=.01,
            refinement=bool(summary['refinement_ok']))
receipt['summary']=summary
receipt['verdict']=dict(checks=checks,**{'pass':all(checks.values())})
complete=(json.dumps(receipt,indent=2,allow_nan=False)+'\n').encode()
expected=json.loads((checkpoints/'completed.json').read_text())['receipt_sha256']
actual=hashlib.sha256(complete).hexdigest()
assert actual==expected,('reconstruction differs from original producer',actual,expected)
gz_path=root/'full-recovered.json.gz'
compressed=gzip.compress(complete,mtime=0)
with gz_path.open('xb') as f:f.write(compressed)
with (root/'full-truncated.json.gz').open('xb') as f:f.write(gzip.compress(raw,mtime=0))
proof=dict(label='Packaging correction only; no model outcomes changed',source_commit=receipt['source_commit'],
           observed_truncated_bytes=len(raw),observed_truncated_sha256=hashlib.sha256(raw).hexdigest(),
           recovered_bytes=len(complete),producer_recorded_sha256=expected,recovered_sha256=actual,
           recovered_gzip_sha256=hashlib.sha256(compressed).hexdigest(),exact_producer_match=True,
           explanation='Aggregate was observed truncated after the producer recorded its complete-file digest. Root cause not established. Reassembled all ten original checkpoints; serialized bytes exactly match producer digest. Original prefix retained.',
           checkpoint_seeds=receipt['seeds'])
with (root/'recovery.json').open('x') as f:json.dump(proof,f,indent=2);f.write('\n')
assert not (root/'full-truncated.json').exists()
raw_path.rename(root/'full-truncated.json')
(root/'full.json.gz').symlink_to('full-recovered.json.gz')
for old,new in [('started.json','run-started.json'),('completed.json','run-completed.json')]:
 with (root/new).open('xb') as f:f.write((checkpoints/old).read_bytes())
print(json.dumps(proof,indent=2))
