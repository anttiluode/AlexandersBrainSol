"""Independent replay of the locked cohort, with no changes to experiment sources.

Run from any directory. Imports are pinned to the clean a67 source worktree.
Only this wrapper's sibling audit artifacts are written.
"""
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial
from pathlib import Path
import gzip
import hashlib
import json
import platform
import subprocess
import sys
import time

LOCK = 'a67f14722f68c3fd91115232970c9a4051ee7825'
SOURCE = Path('/workspace/scratch/33f81f82f09d/alexander-locked')
DEST = Path(__file__).resolve().parent
PARTIAL = DEST / 'full.partial'
sys.path.insert(0, str(SOURCE))
import audit
import experiment as ex
import numpy as np


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_ready(path, timeout=1800):
    deadline = time.monotonic() + timeout
    while True:
        try:
            raw = path.read_bytes()
            return json.loads(raw), raw
        except (FileNotFoundError, json.JSONDecodeError):
            if time.monotonic() >= deadline:
                raise TimeoutError(str(path))
            time.sleep(2)


def reference_checks(protocol):
    return ex.calibrate(protocol), ex.refinement(protocol)


def git(*args):
    return subprocess.check_output(['git', *args], cwd=SOURCE, text=True).strip()


def main():
    output = DEST / 'independent-audit.json'
    if output.exists():
        raise FileExistsError(output)
    assert git('rev-parse', 'HEAD') == LOCK
    assert git('status', '--porcelain') == ''
    assert ex.ROOT == SOURCE
    started, started_raw = load_ready(PARTIAL / 'started.json')
    assert started['mode'] == 'full' and started['source_commit'] == LOCK
    audit.verify_source(started)
    before = ex.hashes()
    protocol = json.loads((SOURCE / 'protocols/switching.json').read_text())
    audit.compare(started['protocol'], protocol, 0, 0)
    calibration_saved = json.loads((SOURCE / 'protocols/calibration.json').read_text())
    means = calibration_saved['means']
    seeds = protocol['full_seeds']
    assert len(seeds) == len(set(seeds)) == 10
    rtol, atol = protocol['audit_rtol'], protocol['audit_atol']
    stats = {'floats': 0, 'max_absolute_difference': 0.0}
    row_checks = {}
    references = None
    print('Verified exact source, start manifest and locked protocol; replay workers=6', flush=True)
    with ProcessPoolExecutor(max_workers=6) as pool:
        reference_future = pool.submit(reference_checks, protocol)
        futures = {pool.submit(ex.run_seed, seed, protocol, means): seed for seed in seeds}
        futures[reference_future] = 'references'
        for future in as_completed(futures):
            seed = futures[future]
            if seed == 'references':
                calibration, refinement = future.result()
                audit.compare(calibration_saved, calibration, rtol, atol, stats=stats)
                original_refinement, raw = load_ready(PARTIAL / 'refinement.json')
                audit.compare(original_refinement, refinement, rtol, atol, stats=stats)
                assert refinement['pass']
                references = dict(calibration=calibration, refinement=refinement,
                                  refinement_checkpoint_sha256=sha(raw))
                print('Replayed full calibration and coupled-Brownian refinement', flush=True)
            else:
                regenerated = future.result()
                original, raw = load_ready(PARTIAL / f'seed-{seed}.json')
                per_seed = audit.compare(original, regenerated, rtol, atol)
                stats['floats'] += per_seed['floats']
                stats['max_absolute_difference'] = max(stats['max_absolute_difference'], per_seed['max_absolute_difference'])
                check = dict(seed=seed, checkpoint_sha256=sha(raw), numerics=per_seed,
                             summary=regenerated['summary'], complete_row_match=True)
                row_checks[seed] = check
                ex.save_new(DEST / f'independent-replay-seed-{seed}.json', check)
                print('Complete trajectory/read/rotor replay matched', seed, per_seed, flush=True)
    assert references is not None and set(row_checks) == set(seeds)
    deadline = time.monotonic() + 1800
    while True:
        receipt_path = DEST / 'full.json'
        if not receipt_path.exists():
            receipt_path = DEST / 'full.json.gz'
        try:
            receipt_raw = receipt_path.read_bytes()
            receipt = json.loads(gzip.decompress(receipt_raw) if receipt_path.suffix == '.gz' else receipt_raw)
            break
        except (FileNotFoundError, json.JSONDecodeError, EOFError):
            if time.monotonic() >= deadline:
                raise TimeoutError('final full receipt did not arrive')
            time.sleep(2)
    assert receipt['mode'] == 'full' and receipt['source_commit'] == LOCK
    audit.verify_source(receipt)
    audit.compare(started['hashes'], receipt['hashes'], 0, 0)
    audit.compare(protocol, receipt['protocol'], 0, 0)
    assert receipt['seeds'] == seeds == [row['seed'] for row in receipt['rows']]
    for row in receipt['rows']:
        original, raw = load_ready(PARTIAL / f"seed-{row['seed']}.json")
        assert sha(raw) == row_checks[row['seed']]['checkpoint_sha256']
        # Final receipt must contain the exact checkpoint, not a merely close one.
        audit.compare(original, row, 0, 0)
    audit.compare(receipt['calibration_means'], references['calibration']['means'], rtol, atol, stats=stats)
    audit.compare(receipt['refinement'], references['refinement'], rtol, atol, stats=stats)
    summary = {key: float(np.mean([row['summary'][key] for row in receipt['rows']])) for key in ex.METRICS}
    summary['refinement_ok'] = bool(references['refinement']['pass'])
    audit.compare(receipt['summary'], summary, rtol, atol, stats=stats)
    audit.compare(receipt['verdict'], ex.verdict(summary), rtol, atol, stats=stats)
    assert ex.hashes() == before and git('rev-parse', 'HEAD') == LOCK
    assert git('status', '--porcelain') == ''
    report = dict(pass_audit=True, receipt_path=str(receipt_path), receipt_sha256=sha(receipt_raw),
                  source_commit=LOCK, source_worktree=str(SOURCE), source_hashes=before,
                  source_verified=True, clean_worktree_verified=True,
                  start_manifest_sha256=sha(started_raw),
                  replay_wrapper_sha256=sha(Path(__file__).read_bytes()), workers=6,
                  runtime=dict(python=platform.python_version(), numpy=np.__version__),
                  tolerances=dict(rtol=rtol, atol=atol), numerics=stats,
                  seeds=seeds, row_comparisons=[row_checks[seed] for seed in seeds],
                  calibration_replayed=True, numerical_refinement_replayed=True,
                  refinement_checkpoint_sha256=references['refinement_checkpoint_sha256'],
                  complete_seed_rows_replayed=True, final_receipt_exactly_matches_checkpoints=True,
                  summary=summary, verdict=ex.verdict(summary))
    ex.save_new(output, report)
    print('INDEPENDENT AUDIT PASSED', json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
