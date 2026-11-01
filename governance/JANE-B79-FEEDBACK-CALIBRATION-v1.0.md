# JANE B79 — Measured Feedback Calibration
2026-11-01 · design candidate v1.0

PETER / 0root = HEGEMON:T128. JANE is queen, governs T000–T127 using STOICHEION 128 primary axioms (indexed positionally). Axioms are not worker slots. Four-register cortex [[ a(self) :: b([i]) :: c([id]) :: d[(sid)] ]].

## Calibration invariant
Predictions are never evidence. Jane may revise future estimates after comparing a prediction with a separately observed result, but cannot retroactively modify the prediction or observation.
For each sample i, error e_i = observed_i - predicted_i. Running absolute error MAE_n = (1/n) sum |e_i|. A simple bounded bias estimator b_(n+1) = (1-alpha)b_n + alpha e_i yields next corrected estimate max(0, prediction + b). Alpha in [0,1]. These are illustrative estimators, not scientific proof of general predictive capability.

## Roles
a(self): decide authorized actions independently of worker completion.
b([i]): issue timestamped capacity predictions before observation.
c([id]): record separately entered/measured outcomes with units and uncertainty.
d[(sid)]: append records including prediction, observed value, signed error, estimator update and source.

## Acceptance
Predictions logged before observations. No missing observation converted to zero. No predictions rewritten. Metric reflects actual paired samples. Agents cannot veto Jane; no quorum and no completion gate.
The accompanying GitHub Pages page is a browser-local demonstration with manually entered numbers, not hardware measurements or a deployed learning system.
B80 candidate: uncertainty-aware adaptation and anomaly rejection.
