# Switching-memory result

Source: `24f9c9b7bf9218ebc10961c0285381f833f4b60a`; mode: **development**.
2 independent noise-seed batches, 48 transition histories, 4800 successive local queries.

| Ring arm | Requested replacement | Old state retained | Reads requested label | Five-query average (secondary) | Any monitored read damage |
| --- | ---: | ---: | ---: | ---: | ---: |
| gated | 100.00% | 0.00% | 93.04% | 99.58% | 0.00% |
| closed | 0.00% | 100.00% | 0.00% | 0.00% | 0.00% |
| gate_only | 33.33% | 33.33% | 29.85% | 33.23% | 0.00% |
| idle | 0.00% | 100.00% | 0.00% | 0.00% | 0.00% |

**Declared overall gate: FAIL.**
Checks: replacement=True, closed_resistance=True, original_idle_retention=True, local_read=False, probe_preservation=True, idle_preservation=True, refinement=True.

Read accuracy in this table means the requested label, with failed writes counted as errors. Closed and idle arms deliberately resist that request; their low requested-label scores are expected. The JSON report separately gives accuracy against the actual valid stored integer. Five-query pooling costs ten time units instead of two and reduces the output rate fivefold. It was identified during development and is a secondary diagnostic, not a replacement for the failed single-query criterion. Temporal queries are correlated; they are not independent trials.

| Ordinary three-well control | Requested replacement | Read correct | Monitored damage |
| --- | ---: | ---: | ---: |
| gated | 100.00% | 100.00% | 0.00% |
| closed | 0.00% | 0.00% | 0.00% |
| gate_only | 0.00% | 0.00% | 0.00% |
| idle | 0.00% | 0.00% | 0.00% |

The ordinary control shows whether the basic gated-memory behavior is generic. Energy, microscopic noise and state dimensions are not matched; these percentages establish no efficiency or topology-specific advantage.

Numerical refinement: {"logical_equal": true, "max_current_error": 0.002932529341280264, "max_field_error": 0.0012798252212220548, "pass": true}.

Scope: prescribed 1D ring, three states, idealized local sensor, engineered write controller, fixed finite time and noise. No learning, grown network, physical mass or permanent protection is established.
