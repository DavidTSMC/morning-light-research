# E005 D-M Event Validation — Research Checkpoint v1.0

## Status
ROBUST VALIDATED CANDIDATE
Not a final trading rule.
Forward out-of-sample validation remains required.

## Core Finding

Direction warns. Event changes state.

- D-M contraction = Direction / Warning
- D-M down-cross of zero = Event / State-change candidate

These two conditions should NOT be treated as equivalent confirmation.

## Locked Validation Design

Universe:
- 2882
- 2330
- 2454
- 0050
- 2603
- 2382

History:
- Approximately 5 years
- Common study period: 2021-08-11 to 2026-08-11

Rules were held constant across stocks.

Cascade context:
Scout -> Bias3 Gate / Bridge -> D-M confirmation

Regime prototype:
- BULL: Close > MA20 and MA20 rising
- BEAR: Close < MA20 and MA20 falling
- SIDEWAYS: otherwise

## Five-Year Pooled Evidence

D-M CONTRACTION
- N = 392
- 3D mean = +0.41%
- 3D negative rate = 41.8%
- 5D mean = +0.93%
- 5D median = +0.76%
- 5D negative rate = 38.8%

D-M DOWN0
- N = 184
- 3D mean = -2.03%
- 3D median = -1.74%
- 3D negative rate = 77.7%
- 5D mean = -2.83%
- 5D median = -2.46%
- 5D negative rate = 71.7%

## Cross-Stock 5D Separation

All six stocks showed the same directional separation:

- 2882: -3.07%
- 2330: -3.57%
- 2454: -3.32%
- 0050: -2.40%
- 2603: -5.39%
- 2382: -5.32%

Negative separation means D-M DOWN0 produced a weaker
5-day outcome than D-M contraction.

## Regime Evidence

BULL
- Contraction N = 243, 5D mean = +1.66%
- DOWN0 N = 152, 5D mean = -2.49%
- Separation = -4.15%

BEAR
- Contraction N = 78, 5D mean = -0.87%
- DOWN0 N = 19, 5D mean = -4.64%
- Separation = -3.78%

SIDEWAYS
- Contraction N = 71, 5D mean = +0.41%
- DOWN0 N = 13, 5D mean = -4.15%
- Separation = -4.56%

## Interpretation

1. D-M contraction should remain a warning/direction signal,
   not be treated as equivalent to a zero-cross event.

2. D-M DOWN0 is a materially stronger bearish-risk candidate
   within the tested Cascade context.

3. Regime is context and may later modify Amount,
   but Entry admission logic and Holding/Exit risk logic
   should remain conceptually separate.

4. Sideways does not imply automatic decline.
   A better working hypothesis is:

   "Sideways alone is not bearish;
    sideways plus momentum breakdown deserves heightened caution."

## Research Limitations

- The hypothesis was developed through iterative exploration.
- Events within one stock are not fully independent.
- Stocks share market/systematic exposure.
- The current results do not establish causal prediction.
- Forward temporal out-of-sample validation is still required.
- No fixed Amount percentage should be assigned yet.

## Frozen Research Principle

Direction warns.
Event changes state.

## Next Independent Experiment

Sideways -> BBAND squeeze -> Duck-Bill expansion
-> Direction -> Momentum confirmation

Purpose:
Study when a Sideways candidate may become eligible
for Elite Pool admission.

Do NOT mix this BBAND experiment into the currently
validated D-M candidate until separately tested.
