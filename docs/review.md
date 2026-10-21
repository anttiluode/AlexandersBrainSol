# Independent pre-lock review

A separate reviewer inspected equations, controls, noise coupling, readout and
source checks before any fresh seed was run. They verified energy/gradient
consistency by finite differences (~2.3e-9 error), found no direct label leakage,
and confirmed the paired probe/no-probe and coupled Brownian refinement design.

Important findings and dispositions:

1. Untracked source could pass a HEAD-only check. The full-run guard now checks
   every implementation/protocol/calibration blob against exact committed bytes.
   Regression uses a real temporary git repository with untracked sources.
2. A destroyed closed control could look resistant to a requested write. Closed
   and idle original-state retention now have their own >=95% gates, and every
   arm reports invalid fractions. A synthetic erasure regression rejects a pass.
3. A late failure could lose outcomes. Outputs are exclusively created, seed
   checkpoints are append-only, and interruptions preserve completed rows and
   aborted metadata. The interruption regression checks surviving first outcome.
4. The original sensor was bare bond coherence. It now measures the covariant
   current conjugate to the energy's applied bond phase. Finite-difference and
   local-gauge tests pin the observable. Original development remains archived.
5. Stale calibration was rejected only at replay. Calibration now carries source
   and protocol hashes checked before fresh outcomes. A stale-dt regression
   rejects execution; final calibration is regenerated under the final source.
6. Per-seed refinement flags were misleading. Numerical validation is global;
   per-row summaries no longer claim independently passing refinement.

Damage means any monitored departure from the post-write state. That is distinct
from successful replacement: failed writes stay in the denominators of write and
read accuracy. Conditional successful-write damage and whole-workflow success
are reported separately. Repeated queries share trajectories, so confidence
intervals, if shown, use independent seed batches rather than individual reads.

The author's regression suite verifies these fixes. This review does not assert
that future fresh outcomes will meet the benefit gate. No reviewer requested
changes to Claude's repositories, which remain untouched.

## Independent full replay and final assessment

The reviewer used a separate clean worktree at exact source lock
`a67f14722f68c3fd91115232970c9a4051ee7825` and a separate preserved replay wrapper.
They regenerated calibration, the complete coupled-Brownian numerical check and
all ten full seeded runs. Every seed row, field, measurement, prediction,
validity/damage flag, ordinary-control output, summary and verdict matched.
468,527 floating-point values were compared at rtol=1e-8 / atol=1e-10; maximum
absolute difference was 0. Discrete outputs matched exactly. Independent recovery
validation proved the complete receipt SHA256 equals the producer's digest and
that the damaged original prefix remains unchanged. Independent arithmetic also
confirmed the secondary read statistics and primary FAIL.

No remaining review blockers. Final author suite: 20 tests passed. The published
source lock and secondary-declaration commits both passed GitHub CPU CI before
results were added. Evidence lives in `results/switching/independent-audit.json`,
`independent-recovery-validation.json`, `independent-claims-validation.json`, and
the ten per-seed audit records. Local filesystem paths in those artifacts record
the original audit environment; use the repository's generic audit.py to replay
the complete gzip receipt elsewhere.
