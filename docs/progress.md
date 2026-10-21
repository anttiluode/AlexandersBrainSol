# Execution record — docs/plan.md

- BrainBoxSol remote branches inspected; both scientific feature heads are
  ancestors of main 9b7b35a; no open PRs. No redundant merge performed.
- New clone on sol/switchable-memory isolates this work from all other repos.
- Design choice: finite 1D amplitude-bearing GL ring, not Claude's 2D code.
  The cost is that this cannot establish 2D phase-slip/geometry behavior.
- Task 1 ring: six tests observed failing because implementation missing;
  implemented covariant operator, energy, validity-aware oracle and local sensor.
- Task 2: experiment and audit tests RED then GREEN (14 total initially).
- First development v1: perfect replacement and closed-state preservation;
  92.71%/92.54% individual 2-time-unit reads; logical state undamaged.
  Raw-current dt refinement failed .005 tolerance (.0223288 at dt=.02).
  A dt=.005 numerical-only development check still missed (.00522946).
  Both are preserved, including exact hash-verified v1 source bytes. Its HEAD
  field is an unlocked baseline, not an implementation/source lock.
- Numerical ruling: reduce dt to .0025, keep all physical durations, noise level
  and numerical/behavioral tolerances fixed. Costs 8x integration work.
- Review fixes: covariant energy-current sensor (finite difference test),
  closed/idle original-state retention, exact committed source verification,
  pre-full calibration binding, append-only completed-seed checkpoints, remove
  misleading per-seed refinement flag. Probe-damage metric means any departure
  from post-write state; failed writes remain in read-accuracy denominator.
- Development v2 dt=.0025: writes=100%, closed/idle retention=100%, per-query
  reads=93.375%/92.7083%; no logical read damage; overall benefit gate FAIL.
  Numerical refinement passes: max field .0012798252, current .0029325293,
  all logical results agree. Full v1/v2 receipts and exact sources retained.
- Added seeded process parallelism (8 workers for full/audit) with exact real
  miniature model comparison to serial and worker-local exclusive checkpoints.
  It changes scheduling only; no new seeds or physical parameters are drawn.
- Full execution refuses fresh seeds if numerical refinement fails.

- Fresh full cohort complete: all ten batches, all 240 writes/closed retentions
  correct, no monitored changes, single-query accuracy 92.7167%; primary FAIL.
  Secondary analog averaging 99.4583%; quantized symbol voting 98.6458%.
- Packaging correction: aggregate observed truncated after producer hashed it.
  Original prefix retained; all ten completed checkpoints reassembled into bytes
  whose SHA256 exactly matches original producer af5d3e10... No model rerun,
  seed selection or interpretation change. Cause of truncation not established.
- Reporting clarification: three labels can be encoded in 2 bits; actual code
  uses integer/JSON storage. No packed-storage efficiency claim is supported.

- Final independent review: no blockers. Calibration, coupled refinement and
  all ten complete seeded runs replayed; 468,527 float comparisons, maxdiff=0;
  exact discrete outputs and summary/verdict. Independent artifact recovery and
  claim arithmetic verified. Author suite 20/20 passes; original lock/declaration
  CPU CI green. All results preserved; primary benefit gate remains FAIL.
