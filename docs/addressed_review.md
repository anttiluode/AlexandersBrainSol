# Addressed-array review and reproduction

21 October 2026. This follow-up changes only AlexandersBrainSol. Claude's repository
was consulted read-only. No first-gate implementation, calibration, protocol or
receipt was replaced.

## Lock and outcome

Source/protocol lock: [23b43c4383e1630e75f21b3218dc8679c6cc4a0e](https://github.com/anttiluode/AlexandersBrainSol/commit/23b43c4383e1630e75f21b3218dc8679c6cc4a0e).
The branch was published and its CPU suite passed before fresh outcomes.
[Source-lock CI](https://github.com/anttiluode/AlexandersBrainSol/actions/runs/39585083966).

Fresh seeds: 1301, 1303, 1307, 1319, 1321. Development uses 1201; sampled paired
refinement uses 1193. No fresh-seed tuning or threshold changes. The
[complete manifest](../results/addressed_updates/full/manifest.json) binds source,
protocol, runtime and both compressed/raw hashes of every per-seed receipt.

Trace/snap/oracle each achieved 120/120 successful pre-read writes, 240/240
bystander exposures without any monitored logical departure, 120/120 correct
whole-array endpoints and 357/360 five-query votes. No post-write read damage
in 360 cell-event episodes per arm. These are 30 repeated histories in five
independent noise batches. The analog-benefit gate fails: zero endpoint gain,
zero batches with positive gain. Ordinary three-well controls get every one of
these operations right. Wrong, all-open and closed access each yield zero
correct whole-array endpoints. Full results and denominators are in the
[report](../results/addressed_updates/report/report.md).

## Review changes before the lock

An independent reviewer identified source-binding gaps, pre/post-read scoring
confusion, a missing read-survival guard in the analog-benefit gate, use of the
wrong bond phase for refinement current, and detection of an already incorrect
monitor reference. These were fixed and regression-tested before the lock and
fresh run. No unresolved Important findings remained. Subsequent independent
review confirmed the final report's denominators and bounded claims.

The 35-test suite passes locally (Python 3.12.14, NumPy 2.3.5, Numba 0.68.0).
Coverage includes controller isolation from hidden fields/targets, symbol-only
latch decisions, cumulative ideal contents, operational/benefit verdicts,
source hashes, and compiled-vs-original dynamics, readouts, random ordering and
transient damage detection. Independent backend review also matched ordinary
trajectories and exact RNG states across eight cases, including a chunk boundary.

## Numerical evidence and archived runtime refinement

The sampled dt/dt2 check covers a complete four-event history in all six arms,
including every write phase and all five queries (216 phase comparisons).
Maximum field difference: 0.0010580938771797132 (limit 0.02). Maximum current
difference: 0.002267216086866919 (limit 0.005). Closed-phase winding and validity
match. This does not refine every fresh history.

The first NumPy development attempt was slow. Its exact source snapshot, raw
seed outcome and end-of-run source-guard rejection remain archived under
`development-source-v1` and `development-v1`. It is not a completed locked run.
A separate faster backend leaves the original ring/writer unchanged.
[Reference comparison](../results/addressed_updates/backend-reference-validation.json)
checks 117,540 floats, maximum difference 3.7192471324942744e-15 at rtol=1e-10,
atol=1e-11, plus exact discrete outputs. Development-v2 completed at the published
lock before the fresh run.

## Interpretation limits

This is selective access to three independent cells under a shared value bias,
not learned memory allocation. Spatial ports, cue reset/trigger timing and desired
values are supplied. The snapped gate decision needs only an integer address;
diagnostic arrays are still computed and archived outside its decision path.
Encodable two-bit information is not a physical two-bit implementation. The
ordinary control prevents a topology-necessity conclusion; its microscopic noise,
state dimension and energy are not matched for efficiency comparisons. Five-query
votes cost five query durations. Neither this gate nor voting retrospectively
rescues the original single-query gate or proves continuous waveform necessity.

## Independent full replay

[Audit](../results/addressed_updates/independent-audit.json) and
[archived wrapper](../results/addressed_updates/independent-replay.py) were run from
an independent clean worktree at the exact lock. Source bytes, original NumPy
sensor calibration and coupled refinement were verified, then both memory media
and all six controllers were rerun for every fresh seed/history/event/read.
The audit checked original compressed and raw receipt digests, all summaries
and gates, and source/wrapper immutability. It compared **588,917 floating values
with zero difference**, using declared rtol=1e-8 and atol=1e-10; **58,535
nonfloating receipt leaves** matched exactly. Raw receipt leaves include 587,700
floats; the larger comparison count also includes metadata/calibration/refinement.
This covers 720 array-event endpoints, 2,160 cell-event endpoints and 10,800
individual primary queries across the six arms. Independent compressed checkpoints
and their manifest are preserved separately. No original receipt was overwritten.
