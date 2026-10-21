# Model, read budget and limits

The real/imaginary components obey overdamped gradient flow with independent
additive Gaussian noise. With material field mu and bond phases a,

F = dx sum( |exp(-i a_j) psi_(j+1) - psi_j|² / (2 dx²)
           + |psi_j|⁴ / 4 - mu_j |psi_j|² / 2 ).

The mobility convention is -grad(F)/dx; each real noise component has increment
variance 2 T dt/dx. The continuum-time stationary density would be exp(-F/T)
under fixed controls. Finite Euler steps approximate that SDE; this is a
phenomenological classical model rather than a physical BEC reproduction.
The energy-current sensor is -dF/da at one bond. Its sign distinguishes the
three stored circulation labels after calibration.

The lattice winding is an audit of the interpolated closed field. A node
amplitude below .15 or any phase jump >=.8 pi invalidates it. No winding claim
is made while the gate is open. Read monitoring checks every integration step,
including invalidity and a departure that later returns. This does not observe
continuous sub-step events. The coupled Brownian check uses one fixed numerical
seed and all six transition types, four arms, write phases and 100 query
endpoints; it is not a second independent refinement of all fresh histories.

The weak read phase (.005) is held on one bond throughout the 100-query read
sequence. It is a persistent weak probe, not 100 independent probe pulses.
The no-probe copy has identical elapsed time and paired process noise. Sensor
noise is independently added after time averaging; there is no dynamical
receiver model or measured sensing energy.

## Fixed budgets

- Ring memory: 64 complex128 field values = 1,024 bytes of dynamical state.
  This excludes controls, RNG, observation buffers, Python and numerical caches.
- Ordinary control: one float64 angle = 8 bytes. Its barrier/drive units and
  microscopic noise are not matched to the ring; no efficiency comparison.
- Three logical labels: at most log2(3) information bits, encodable as 2-bit codes. The code actually uses integer arrays/JSON, not bit-packed storage.
- One primary query: five local samples averaged over two time units; one noisy
  float64 scalar enters the frozen three-level decoder. 100 correlated queries.
- Secondary analog mean: five primary scalar values, ten time units.
- Secondary symbol vote: the same five primary queries, only the five decoded
  three-state symbols retained (encodable with 2 bits each). Strict majority required; abstention counts wrong.
  It has no hidden analog magnitude input. Float representation width is not
  a claim of equally many noise-free physical bits.

Each transition history and each ring arm uses 144,000 write/wait integration
steps plus 80,000 probed and 80,000 paired no-probe steps at dt=.0025. A vectorized
batch contains 24 histories. Ten batches and four arms therefore use 12,160,000
vectorized field updates, or 18,677,760,000 site-history updates. These counts
exclude calibration, timestep refinement, independent replay, decoding/reporting
and Python allocation. The ordinary control lacks a no-probe copy and is not
cost-matched.

Each history tests one requested replacement of an analytically prepared old
state, followed by reading. It does not establish long sequences of repeated
write/read/replace cycles, addressing between multiple rings, physical
robustness, a learned network, or a switching-threshold curve. Two gate settings
(open versus closed) test selective access. Zero observed damage is finite-time
evidence at this noise strength, not a lifetime guarantee.
