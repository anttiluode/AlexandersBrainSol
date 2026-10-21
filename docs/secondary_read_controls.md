# Secondary read controls, declared before fresh outcomes

Primary source/protocol: a67f14722f68c3fd91115232970c9a4051ee7825.
The full run has started. As of this declaration no fresh seed result checkpoint
exists; only the numerical refinement phase has run. These are descriptive
controls and do not change the primary 95% single-query gate or model settings.

Development suggested that averaging five successive scalar sensor values could
improve accuracy. To avoid confusing preserved analog magnitude with the benefit
of repeated measurement, report both:

- Analog mean of five query values, then the same frozen calibration thresholds.
- Strict majority of five already-quantized query symbols (-1,0,+1), each stored
  with two bits. Without three matching symbols, abstain and count the read wrong.
  No means, raw magnitudes, hidden fields or requested labels enter the voter.

Both consume the same ten physical time units, versus two for a single query.
There are 20 disjoint five-query groups per history; these groups still share a
trajectory and are not independent experimental units. Report vote coverage.
The raw analog measurements are stored as float64 values; that representation
is not a claim of 64 noise-free physical information bits. The voter consumes
10 storage bits, with an entropy cap of 5 log2(3) bits before correlations.

A good vote result would show that retaining analog magnitude after each query
is unnecessary for this limited repeated-read task. It says nothing about
whether the continuous dynamics inside the ring can be eliminated, and does not
show any advantage over ordinary three-state memory.
