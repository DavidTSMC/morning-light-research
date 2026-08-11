# Duck-Bill Transition & Relay Validation — Research Checkpoint v1.0

## Status
CROSS-STOCK SUPPORTED RESEARCH CANDIDATE

Not a final trading rule.
Not yet forward out-of-sample validated.
Do not add further indicators before independent validation.

## Core Architecture

SIDEWAYS / SQUEEZE
    ->
BBAND EXPANSION
    ->
D-M MOMENTUM RELAY
    ->
DI OSC DIRECTIONAL RELAY / RESONANCE
    ->
MTM3 PRICE-THRUST VALIDATION
    ->
EMERGING TREND / ELITE ADMISSION CANDIDATE

## Core Research Principles

1. State is not Event.
2. Sideways and Expansion must be temporally separated.
3. BBAND primarily detects volatility transition, not direction by itself.
4. Evidence may propagate through time.
5. Cascade and Resonance can coexist.
6. More indicators do not automatically mean more information.

## Duck-Bill v0.1

Initial condition required:

SIDEWAYS AND EXPANSION on the same day.

Result:
- SIDEWAYS observations existed.
- SQUEEZE observations existed.
- EXPANSION observations existed.
- SIDEWAYS + EXPANSION = 0 across all six stocks.

Interpretation:
Logical-definition failure.

Sideways is a State.
Expansion is an Event that may represent leaving that State.

## Duck-Bill v0.2 — Temporal Transition

Definition:

Recent Sideways + Squeeze
    ->
Today BBAND Expansion

No momentum filters were used.

Pooled Duck-Bill events:
- UP N = 227
- DOWN N = 269

UP:
- 10D mean = +1.45%
- 10D positive rate = 58.6%

DOWN:
- 10D mean = -0.72%
- 10D negative rate = 53.5%

Interpretation:

BBAND expansion contains modest directional information,
but is better treated as a Transition Detector than
a standalone directional predictor.

## Duck-Bill v0.4 — Temporal Relay

Test:

T0 Duck-Bill Expansion
    ->
T+1 to T+5 D-M relay
    ->
T+1 to T+5 DI Osc relay

D-M and DI Osc were tested separately.

### BOTH vs NEITHER — pooled 10D

UP:
- BOTH N = 171
- mean = +2.94%
- success = 70.8%

- NEITHER N = 24
- mean = -4.43%
- success = 16.7%

DOWN:
- BOTH N = 204
- mean = -1.98%
- bearish success = 63.7%

- NEITHER N = 19
- mean = +5.66%
- bearish success = 10.5%

Interpretation:

Duck-Bill expansion without momentum follow-through
has substantial failed-expansion risk.

D-M + DI Osc relay resonance materially improves
directional follow-through.

## Duck-Bill v0.5 — Cross-Stock Consistency

10D BOTH vs NEITHER separation:

2882:
- UP = +9.75%
- DOWN = +7.32%

2330:
- UP = +5.24%
- DOWN = +7.50%

2454:
- UP = +8.52%
- DOWN = +5.89%

0050:
- UP = +5.81%
- DOWN = +6.03%

2603:
- UP = +7.22%
- DOWN = +9.83%

2382:
- UP = +8.33%
- DOWN = +8.42%

All 12 stock-direction comparisons showed
the expected direction of separation.

Important limitation:
NEITHER sample sizes were small in several stocks.
Therefore effect direction is more trustworthy
than effect magnitude.

## Duck-Bill v0.6 — MTM3 Incremental Value

Question:

Does MTM3 add information after D-M + DI Osc BOTH relay?

### UP — D-M + DI BOTH already present

MTM NO RELAY:
- N = 12
- 10D mean = -1.46%
- success = 41.7%

MTM DIRECTION:
- N = 97
- 10D mean = +2.99%
- success = 73.2%

MTM ZERO CROSS:
- N = 62
- 10D mean = +3.73%
- success = 72.6%

### DOWN — D-M + DI BOTH already present

MTM NO RELAY:
- N = 13
- 10D mean = +3.90%
- bearish success = 30.8%

MTM DIRECTION:
- N = 88
- 10D mean = -3.16%
- bearish success = 68.2%

MTM ZERO CROSS:
- N = 103
- 10D mean = -1.71%
- bearish success = 63.1%

Interpretation:

MTM3 provides incremental information.

Its most useful role is currently:

PRICE-THRUST VALIDATION

not:

EARLIEST ALERT.

## Lead / Lag

When all three relays were present:

UP:
- D-M mean lag = 1.38 days
- DI Osc mean lag = 1.62 days
- MTM3 mean lag = 2.18 days

DOWN:
- D-M mean lag = 1.51 days
- DI Osc mean lag = 1.90 days
- MTM3 mean lag = 2.52 days

Current evidence therefore suggests:

D-M = earlier momentum relay
DI Osc = directional relay / resonance
MTM3 = later price-thrust validation

However, many events occurred on tied relay dates.
Do not impose a rigid mandatory sequence without
additional validation.

## Cross-Stock — All Three Relay

10D mean outcomes:

2882:
- UP +3.03%
- DOWN -1.45%

2330:
- UP +2.45%
- DOWN -1.55%

2454:
- UP +4.57%
- DOWN -5.00%

0050:
- UP +4.02%
- DOWN -0.60%

2603:
- UP +3.28%
- DOWN -4.30%

2382:
- UP +2.82%
- DOWN -1.54%

All six UP means were positive.
All six DOWN means were negative.

## Important Event-Hierarchy Finding

MTM3 zero-cross was NOT consistently superior
to MTM3 directional relay.

Therefore:

Different indicator families should not automatically
share the same event hierarchy.

Do not assume:
ZERO CROSS > DIRECTION
for every indicator family.

## Elite Pool Working Hypothesis

SIDEWAYS
    ->
Observation Pool

SIDEWAYS + SQUEEZE
    ->
Compression / Watch

Duck-Bill Expansion
    ->
Transition Candidate

D-M + DI Osc relay
    ->
Momentum Resonance / Emerging Trend

MTM3 relay
    ->
Price-Thrust Validation

All confirmed
    ->
Elite Admission Candidate

This remains a research candidate,
not a final admission rule.

## Research Limitations

- Rules were developed through iterative exploration.
- Events are not fully statistically independent.
- The six stocks share systematic Taiwan-market exposure.
- NEITHER groups were small for several individual stocks.
- Effect magnitude is not yet stable.
- No causal claim is established.
- Forward temporal out-of-sample validation is required.
- Do not add additional indicators merely to improve historical fit.

## Frozen Working Principles

BBAND detects transition.

D-M relays momentum.

DI Osc contributes directional resonance.

MTM3 validates price thrust.

Cascade may lead into Resonance.

## Next Step

Freeze this candidate.

Do not add J, W/R, RSI, Volume, or other indicators
until separately justified.

Next major validation:
Forward / temporal out-of-sample testing.

