# Switching-memory result

Source: `a67f14722f68c3fd91115232970c9a4051ee7825`; mode: **full**.
10 independent noise-seed batches, 240 transition histories, 24000 successive local queries.

| Ring arm | Requested replacement | Old state retained | Reads requested label | Five-query analog average | Five-query symbol vote | Any monitored read damage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| gated | 100.00% | 0.00% | 92.72% | 99.46% | 98.65% | 0.00% |
| closed | 0.00% | 100.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| gate_only | 33.33% | 33.33% | 29.47% | 32.98% | 32.46% | 0.00% |
| idle | 0.00% | 100.00% | 0.00% | 0.00% | 0.00% | 0.00% |

**Declared overall gate: FAIL.**
Checks: replacement=True, closed_resistance=True, original_idle_retention=True, local_read=False, probe_preservation=True, idle_preservation=True, refinement=True.

Read accuracy in this table means the requested label, with failed writes counted as errors. Closed and idle arms deliberately resist that request; their low requested-label scores are expected. The JSON report separately gives accuracy against the actual valid stored integer. Five-query pooling costs ten time units instead of two and reduces the output rate fivefold. It was identified during development and is a secondary diagnostic, not a replacement for the failed single-query criterion. The quantized control uses only five already-rounded three-state symbols (encodable in 2 bits each; the implementation stores integers); it requires a strict majority, counts abstentions as errors, and has no access to analog magnitudes. The analog average retains five floating scalar measurements. Both secondary controls use the same five queries and cannot rescue the primary gate. Temporal queries are correlated; they are not independent trials.

| Ordinary three-well control | Requested replacement | Read correct | Monitored damage |
| --- | ---: | ---: | ---: |
| gated | 100.00% | 100.00% | 0.00% |
| closed | 0.00% | 0.00% | 0.00% |
| gate_only | 0.00% | 0.00% | 0.00% |
| idle | 0.00% | 0.00% | 0.00% |

The ordinary control shows whether the basic gated-memory behavior is generic. Energy, microscopic noise and state dimensions are not matched; these percentages establish no efficiency or topology-specific advantage.

Numerical refinement: {"logical_equal": true, "max_current_error": 0.002932529341280264, "max_field_error": 0.0012798252212220548, "pass": true}.

Scope: prescribed 1D ring, three states, idealized local sensor, engineered write controller, fixed finite time and noise. No learning, grown network, physical mass or permanent protection is established.
