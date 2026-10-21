# Addressed updates: bounded follow-up

Antti authorized continuation in AlexandersBrainSol on 21 October 2026. This
experiment tests whether the existing writer can serve a small selectively
updated memory array, and whether analog address eligibility is necessary.
It does not infer a teacher, learn semantic addresses, grow rings, or learn
which values matter. The externally supplied value remains a command.

## Why this gate

The first gate tested one analytically prepared cell and one replacement.
An array must update one cell without rewriting closed neighbours, including
when later requests return to an earlier cell. Coupling here is a shared write
bias; the three rings otherwise have independent fields, not spatial interactions.
Before learning routes, establish that a local access policy actually controls
this complete repeated write/hold/read/update workflow.

Claude's comparison at AlexandersBrain eccf197 is useful but its gate-only
interpretation needs correction: our first 240 gate-only outcomes were ALL n=0.
33.33% was requested-label accuracy, not uniform random output. No changes to
Claude's repositories are made here. We preserve every first-gate receipt.

## Task and controller

Six histories cover all permutations of initial three-cell contents {-1,0,+1}.
Four updates visit each cell and return once to the first, with address order
rotated across histories. The intended value advances that cell's ideal label
cyclically; requests are prepared without consulting actual fields or readers.
After initial preparation fields are never set from labels.

Each event supplies six noisy spatial cue samples to three ports, then three
noisy blank-delay samples. A nonnegative eligibility trace updates by
m <- decay*m + (1-decay)*max(cue,0). A trigger chooses argmax(m).
At cue end, a paired discrete latch saves only the argmax address and retains
that symbol through the delay; no analog trace, field, or target index is read
by that latch during delay. Both use the same cue accumulator and cue/trigger
markers. The analog trace keeps integrating background activity through delay.
Controller sampling is a separate clock. Both cue accumulators are explicitly
reset at each cue onset; the analog trace persists through the noisy delay,
whereas the snapped controller retains only its address symbol. The gate choice
is held throughout actuation. These engineered boundary
conditions are explicit, not a claim that slow material autonomously learns.

Six paired arms: analog trace, snapped latch, oracle (external address), cyclic
wrong address, all-open, all-closed. At actuation the value bias is broadcast to
all three cells. Only opening a cell's six-site weak link permits writing.
Each event uses the original writer's durations, dt, temperature and frozen
one-bond sensor. Read five primary queries and report symbol-majority accuracy;
readouts never enter control decisions. Track bystander logical changes at
every integration step during actuation and read, not only final labels.

Ordinary three-well cells receive the identical gate decisions and commands,
with original barrier/drive settings. They remain a mechanism comparison,
not an energy/dimension/noise-normalized efficiency benchmark.

## Gates locked before fresh outcomes

Operational gate for each controller: routing >=95%, valid requested writes
>=95%, no monitored bystander changes in >=99% of bystander exposures,
whole-array intended contents correct on >=95% of event endpoints, symbol-voted
read accuracy >=95%, and numerical refinement pass. Failed earlier writes stay
in later whole-array denominators. Read damage remains separately reported.

A separate analog-benefit gate requires >=5 percentage points improvement over
the snapped latch in whole-array endpoint accuracy, positive paired difference
in >=80% of fresh seed batches, and no bystander-protection/read-cost penalty.
This is a probe of analog eligibility under this input schedule, not richer
waveform necessity, topology necessity, or general learning superiority.

Numerical check uses coupled Brownian increments at dt and dt/2 for all six
arms, the complete four-event sequence in one canonical history, and all five
read queries. Require max field difference <=.02, max local sensor-current
difference <=.005, identical closed-phase winding/validity. It is a sampled
refinement, not a refined replay of every fresh history.

Freeze new source/protocol before five fresh seed batches. Development uses
separate seeds; preserve all development, including failures. Store one complete
compressed receipt per seed plus manifest/digests, so a large aggregate cannot
lose all raw outcomes. A separate replay verifies source provenance, calibration,
full controller and field trajectories, counts, verdict and original digests.
No tuning fresh seeds. Merge reviewed completed work with a merge commit.

## Budgets and limits

The analog eligibility uses three float64 values (24 bytes); the snapped address
has three symbols, encodable in two bits, actually stored as an integer. Both
have an ephemeral three-value cue accumulator and a latched gate register for
actuation. A global command is another three-state symbol. Every ring uses 64
complex128 values (1024 bytes); each ordinary cell uses one float64 angle. These
are not full implementation RAM or physical information/energy budgets.

Initial labels are analytic; the addressed replacements and subsequent updates
must be dynamical. No physical inter-ring coupling, semantic input, learned
address mapping, self-supervised objective, capacity scaling, long lifetime,
or threshold-curve advantage is established by this test.

## Implementation and review notes before fresh outcomes

The original NumPy-only runtime calibration is retained under development-v1
with its exact uncommitted source snapshot. It is not a source-locked full run
and no independently locked audit is claimed for that attempt. Its seed finished,
but the end-of-run source guard correctly rejected the changed checkout. The raw
receipt and explicit abort record are preserved, without a completion manifest. The new array
backend implements the same Euler equations and NumPy random increment order
using Numba (pinned separately). It does not modify ring.py or the first gate.
Seeded tests compare fields, monitor flags/minimum amplitudes, physical current
readout and ordinary dynamics against the original NumPy implementation. Large
phase jumps and a transient winding departure followed by a return are covered.

The monitor shortcut only applies when node phase increments and old/new bond
phases lie in their positive complex half-planes. This excludes a branch crossing;
otherwise it calculates the full winding sum. A full evaluation on the first
step catches an already mismatched reference. Sticky damage skips only redundant
later winding evaluations, while still tracking minimum amplitude.

Independent review caught and regression tests pin: imported comparator and
backend source hashes; pre-read writer scoring; read-survival protection in the
analog-benefit gate; physical bond phase in numerical sensor comparisons; and
wrong-reference detection in the compiled monitor. Current-source calibration
remains unchanged and bound to its original first-gate implementation.

## Locked outcome

The exact source/protocol commit is 23b43c4383e1630e75f21b3218dc8679c6cc4a0e.
Development-v2 and the five fresh batches use it without retuning. Trace, snap and
oracle each pass: 120/120 writes, 240/240 protected bystander exposures, 120/120
correct whole-array endpoints and 357/360 correct five-query votes. All 360
cell-event probe episodes preserve their post-write state. The analog-benefit
gate fails (zero gain, zero positive batches). Ordinary three-well counterparts
are perfect on these operations. Every negative access control has zero correct
whole-array endpoints. These are correlated repeated histories in five independent
noise batches, not 120 independent devices.

All 117,540 floating values in the archived original NumPy development receipt
and compiled development-v2 agree at rtol=1e-10, atol=1e-11; maximum absolute
difference is 3.72e-15. Discrete labels and monitor flags match exactly. This
checks the faster backend without promoting the source-guard-aborted development
attempt to confirmation. See backend-reference-validation.json and the independent
full replay for distinct numerical-equivalence and reproducibility evidence.

The snapped decision depends only on its retained integer address. Shared
instrumentation still computes and records cue/trace arrays outside its gate
choice; this establishes address-symbol sufficiency, not a physical two-bit
implementation or measured memory/energy savings. A stronger corruption or
capacity regime was not explored after the fresh result.
