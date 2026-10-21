# Selectively switchable memory: first experiment

Antti authorized autonomous implementation on 2026-10-21 in AlexandersBrainSol.
Claude's AlexandersBrain and BrainBoxClaude remain read-only. BrainBoxSol's
bridge-audit and local-slowness branches are already ancestors of main
(merge commits 6bce94e and 9b7b35a). No old receipts are moved or rewritten.

## Question and choice

Does lowering a local barrier allow deliberate replacement of a stable logical
state while a weak, target-independent local read leaves that state intact?
The earlier BrainBoxSol material trace retained old cues but resisted replacement.
This experiment asks about selective access, not maximal stability.

Three possible starts: a full two-dimensional annulus (closest to Claude but
expensive), a one-dimensional complex ring (chosen, permits amplitude collapse
and phase slips), or a phase-only rotor (useful conventional control but omits
phase-slip cores). Start with the smallest field model and an ordinary three-well
control. No claim about Alexander horned spheres, neurons, learned networks,
physical mass, or advantage over conventional memory is intended.

## Ring and access

A periodic complex Ginzburg-Landau field uses a gauge-covariant nearest-neighbor
Laplacian, positive cubic damping, and independent additive Gaussian components.
A short segment's material parameter can be lowered. During writing a uniform
bond gauge favors the requested winding (-1,0,+1); restore the segment before
removing the gauge. No field is overwritten after initial preparation. Test every
ordered pair of different initial and requested states. Initial preparation is
analytic and is NOT counted as successful writing.

Four paired arms: gated command, identical command with gate closed, gate-only
(no command), and idle. The last two are diagnostics: opening alone may erase.
After writing, remove all target information and controllers. Wait, then read
through one bond far from the gate using a weak local gauge perturbation. A
calibrated scalar current decoder sees only this local measurement, never the
full-field winding or requested label. Freeze calibration before full seeds.
Compare paired no-probe trajectories over the same elapsed time. Repeated reads
must retain the written integer, not merely produce a stable mean output.

A scalar angle in a conventional three-well potential gets a separately
calibrated barrier-lowering command. It has the same three labels and read count,
not matched microscopic energy, time, dimension or physical noise temperature.
It prevents attributing the mere existence of gated memory to topology. It is
not a hardware performance benchmark.

## Evidence and gates

Development seeds and every development outcome stay labeled development.
Publish exact source/protocol lock before fresh seeds. The full receipt stores
per-trial initial/requested/actual winding, validity, read errors, state changes,
control costs, RNG and source metadata. A separate replay audit never overwrites
it. Endpoint numerical comparisons use declared tolerances; identical source,
protocol and seeds are mandatory. Deterministic dt-halving checks keep physical
phase durations fixed. Fresh seed outcomes cannot be used for tuning.

Success requires reliable replacement (>=95%), closed-gate resistance (<=5%
replacement), >=95% local read accuracy, <=1% monitored logical changes over
repeated reads, comparable idle preservation, and numerical refinement. All gates
are conjunctive; conventional control success is reported regardless. Rejection
of any condition is a useful result, not permission to tune fresh seeds.

## Limitations

Finite time, small state alphabet, engineered gauge and barrier controllers,
phenomenological thermal convention, idealized local sensor with explicit added
noise, and a discrete 1D ring. Positive results would establish a simulated
component at these settings. They would not establish a 2D/3D device, an energy
advantage, perpetual protection, or topology-specific superiority.

## Primary precedent

Wright et al., Driving phase slips in a superfluid atom circuit with a rotating
weak link, PRL 110, 025302 (2013), https://arxiv.org/abs/1208.3608.
Eckel et al., Hysteresis in a quantized superfluid atomtronic circuit, Nature 506,
200 (2014), https://www.nist.gov/publications/hysteresis-quantized-superfluid-atomtronic-circuit.
These motivate tunable barriers; this GL simulation is not a reproduction.
