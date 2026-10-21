# Addressed update implementation

1. Test controller integration, discrete-latch information restriction, balanced
   request generation, and operational/analog-benefit failure conditions first.
   Add addressed_updates.py reusing ring.py and the existing frozen calibration.
2. Test and add broadcast-bias gated array evolution, bystander monitoring,
   ordinary control, full history receipts, sampled coupled refinement, exact
   source guards and append-only compressed seed files with manifest hashes.
3. Run one development batch, preserve its source and outcome. Independent
   review checks cue/content separation, all denominators and bystander/read
   monitoring. Fix important defects before source lock; no original source edits.
4. Publish source/protocol lock, run five fresh batches once, independently
   replay all complete histories, publish concise report and one scientific
   visualization, verify tests/CI and merge. Any numeric/benefit failure stays
   explicit; no fresh-seed tuning.

Performance ruling: preserve the first NumPy-only runtime attempt and source,
add a separately validated compiled backend for this follow-up only. It keeps
the same SDE, time step, noise order, read budget and scientific gates; costs a
Numba dependency and explicit equivalence/monitoring tests. New requirements
pin NumPy2.3.5 and Numba0.68.0. Original first-gate source remains unchanged.
