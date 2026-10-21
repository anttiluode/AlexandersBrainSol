# AlexandersBrainSol

A small falsification-first study of **selectively switchable memory**:
write a winding number by opening a weak link, close it to retain the number,
read locally, and intentionally replace it later. This is a finite classical
simulation, not an Alexander horned sphere, a grown brain, or a claim of novel
physics. Claude works separately in [AlexandersBrain](https://github.com/anttiluode/AlexandersBrain).

The motivation is [BrainBoxSol's local-slowness result](https://github.com/anttiluode/BrainBoxSol/pull/8):
slowing improved retention but resisted updating. Here the proposed solution is
an explicit write gate, not more permanent stability.

## Addressed-array result — 21 October 2026

[Report](results/addressed_updates/report/report.md) · [Protocol](protocols/addressed_updates.json) · [Complete per-seed receipts](results/addressed_updates/full/manifest.json) · [Design and limits](docs/addressed_updates.md)

A three-cell array now performs four successive updates, including returning to
the first cell. A noisy spatial cue chooses which local gate opens; a value bias
is broadcast to all three cells. The source and protocol were published at
[`23b43c4`](https://github.com/anttiluode/AlexandersBrainSol/commit/23b43c4383e1630e75f21b3218dc8679c6cc4a0e)
before five fresh noise-seed batches (30 three-cell histories).

| Fresh result, per controller | Analog trace | Discrete address latch | Oracle address |
| --- | ---: | ---: | ---: |
| Correct requested writes before reading | 120/120 | 120/120 | 120/120 |
| Neighbor-cell exposures without monitored damage | 240/240 | 240/240 | 240/240 |
| Correct whole-array update endpoints | 120/120 | 120/120 | 120/120 |
| Five-query voted reads of intended contents | 357/360 | 357/360 | 357/360 |
| Cell-event read episodes without damage | 360/360 | 360/360 | 360/360 |

All three pass the new operational gate. **The analog-benefit gate fails:**
the continuous trace adds zero percentage points over an address symbol.
This is a sufficiency result for the engineered cue/delay schedule; diagnostic
analog arrays remain archived, and no packed two-bit hardware is implemented.
The ordinary three-well array reaches 100% on the same operations, including
reading. Wrong-address, all-open and closed controls each get zero correct
whole-array endpoints. Access matters; no topology advantage is demonstrated.

The controller is engineered, the spatial ports define addresses, and requested
values are externally supplied. This establishes selective access and reuse of
a small memory bank. It does not learn where or what to store. Five-query reading
costs five times the query duration and does not repair the first experiment's
failed single-query gate. Numerical refinement passes; see the
[review and reproduction record](docs/addressed_review.md) for independent audit
and test evidence. All original code and receipts remain preserved.

## First single-cell result — 21 October 2026

[Report](results/switching/report.md) · [Full receipt](results/switching/full-recovered.json.gz) · [Recovery correction](results/switching/recovery.json)

Ten independent noise-seed batches, 240 transition histories, 24,000 local
queries under source lock [`a67f147`](https://github.com/anttiluode/AlexandersBrainSol/commit/a67f14722f68c3fd91115232970c9a4051ee7825).

| Test | Result |
| --- | ---: |
| Requested gated replacements | 240/240 |
| Closed-command old-state retention | 240/240 |
| Histories with monitored probe damage | 0/240 |
| Single-query accuracy | 92.72% |
| Five-query analog mean, secondary | 99.46% |
| Five-query symbol majority, secondary | 98.65% |

**The declared overall gate fails:** individual queries miss the 95% accuracy
criterion. Gated replacement and finite-time integer preservation work at these
settings. Repeated already-quantized labels suffice for >95% secondary accuracy;
retaining analog magnitudes helps slightly, with no necessity claim. Both
five-query controls cost five times the query duration. The conventional
three-well control also performs gated replacement and reaches 100% read accuracy;
there is no demonstrated topology or efficiency advantage.

The original **20 tests passed**. An [independent full replay](results/switching/independent-audit.json) compared **468,527 floats with zero difference**, plus exact discrete outputs, under the original source lock.

A truncated aggregate copy was recovered from the original completed seed
checkpoints. The recovered bytes exactly match the complete-file SHA256 recorded
by the producer. The original prefix, expected digest, recovery script and a
labeled correction remain available. No model, seeds, thresholds or outcomes
were changed. See [method and costs](docs/method_and_costs.md) for physical,
numerical and storage limits.

## What the first test measures

A 64-site complex Ginzburg-Landau ring stores one of three windings (-1,0,+1).
The write controller lowers six sites' material parameter and applies a uniform
bond bias favoring the requested winding. It restores the material before
removing the bias. After analytic initial preparation, no field is overwritten
with a requested state. Every transition is between distinct labels.

Four arms share initial states, noise draws, elapsed time and requested label:

| Arm | Lowered barrier | Requested bias |
| --- | --- | --- |
| Gated command | Yes | Yes |
| Closed command | No | Yes |
| Gate only | Yes | No |
| Idle | No | No |

A target-independent weak perturbation reads one local covariant bond current,
far from the write gate. Five samples over two time units produce one noisy
scalar, decoded using separate frozen calibration. There are 100 successive
queries. Full-field winding is an audit oracle only. Every integration step
checks for logical departures and invalid amplitude/phase states; a returning
slip is still counted as damage. A paired no-probe copy separates read effects
from equal-time background noise.

A conventional scalar angle in a three-well potential provides the same logical
alphabet and a barrier-gated command. Physical energy, microscopic noise and
state dimension are not matched, so it is a mechanism control, not a speed or
energy benchmark. Three states carry at most log2(3) information bits (encodable with 2-bit
codes; this implementation stores integer/JSON values); neither continuous field size nor analog sensor precision is free.

## Reproduce

Python 3.12, NumPy 2.3.5 and Numba 0.68.0 reproduce the complete suite.
The original single-cell experiment itself requires only NumPy.

```sh
pip install -r requirements-addressed.txt
python -m unittest discover -s tests -v
# Development uses only seeds 101 and 103 and refuses existing output paths:
python experiment.py development --output /tmp/development.json
# Full execution requires clean checkout of the published exact source lock:
python experiment.py full --lock SOURCE_COMMIT --output /tmp/full.json
# Replay writes a different audit and preserves every original receipt:
python audit.py results/switching/full-recovered.json.gz --output /tmp/full-audit.json
# Three-cell follow-up: use the exact published source checkout for full runs:
python addressed_updates.py development --output-dir /tmp/array-development
python addressed_updates.py full --lock 23b43c4383e1630e75f21b3218dc8679c6cc4a0e --output-dir /tmp/array-full
python addressed_audit.py results/addressed_updates/full --output /tmp/array-audit.json
```

Each worker checkpoints its completed seed outcome before returning it to the coordinator. Full runs
verify source blobs at the locked commit and calibration source/protocol hashes.
The coupled-noise timestep refinement covers every write phase and all 100
read episodes for all six transitions and all four arms. The overall pass gate
requires replacement >=95%, closed-command replacement <=5%, closed and idle
old-state retention >=95%, per-query local read >=95%, monitored read and
no-probe damage <=1%, and the predeclared numerical tolerances.

## Development is not confirmation

The first development had perfect writing and closed-gate preservation but only
about 92.6% per-query read accuracy. Its instantaneous-current timestep check
also failed. Those outcomes and exact source bytes are retained under
`results/switching/development-*`. Decreasing the step fixes numerical precision
only; physical durations, noise, and read/benefit thresholds remain unchanged.
A five-query average looked better in development, but is a secondary diagnostic
and cannot rescue the declared individual-query gate.

See [design](docs/design.md), [protocol](protocols/switching.json),
[review and changes](docs/review.md), and [execution record](docs/progress.md).

## Established precedent

Tunable weak links and phase slips are established physics. The experiment is
inspired by [Wright et al. (2013)](https://arxiv.org/abs/1208.3608) and
[Eckel et al. (2014)](https://www.nist.gov/publications/hysteresis-quantized-superfluid-atomtronic-circuit).
It does not reproduce those experiments or establish a topology-specific
advantage. Finite simulation time cannot prove indefinite protection.
