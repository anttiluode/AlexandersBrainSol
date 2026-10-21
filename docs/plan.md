# Implementation and verification plan

1. Test and implement ring gradient flow, valid winding diagnostics, gate and
   gauge controller, energy descent, label-blind one-bond current readout, and
   ordinary three-well memory. Verify zero/noisy evolution and reproducible RNG.
2. Test and implement paired switching/idle/probe trajectories, frozen scalar
   calibration, gate aggregation, source/protocol guards and separate replay.
   Test that invalid states, failed writes, read damage and label leakage cannot
   yield a pass; missing rows and source changes invalidate receipts.
3. Run clearly labeled development only, preserve results. Independent review
   checks equations, controls, inference and numerical checks before source lock.
4. Publish a clean source/protocol commit, run untouched full seeds once,
   preserve all outcomes, and independently replay. Document null results as
   prominently as positive ones. Run the complete suite, publish a concise
   report and integrate reviewed work with a merge commit.

Review focus: lattice phase aliasing/amplitude zeros; source/calibration leakage;
failed writes hidden by conditional scoring; probe-induced slips that return;
controller changes compared at unequal durations. Each needs an explicit test
or a sampled trajectory diagnostic, with the latter's limits stated.
