# Inheritance study — declared before executing trials

Production remains unchanged. Trait audit: founders use uniform integers 20..80;
eligible local parent pairs succeed with floor((fertility A+fertility B)/3)/1000;
child traits clamp(floor((A+B)/2)+uniform integer[-10,10],0,100).

Mathematical populations: 20 independent seeds 1..20; 60 individuals, six traits,
1,000 discrete generations. Initialize from each seed's actual founder traits.
Separate deterministic NumPy PCG64 streams for parents, mutation and rounding.
Match parent proposals/mutation arrays across comparisons wherever possible;
changed selection weights necessarily change selected parents and later states.

Conditions: current floor with +/-10 mutation; unbiased stochastic half rounding
with the same mutation; floor with no mutation; unbiased rounding with no mutation;
floor with +/-5 mutation. All retain 0..100 bounds. No ecology/survival. Record
parent average, pre-clamp rounding error, mutation increment, clamp increment,
trait means/dispersion at generations 0,10,50,100,250,500,1000. Paired seed differences
and bootstrap 95% intervals (fixed independent resampling stream); these describe
this experiment, not fitness in the full game. Analytical floor error is -0.5 for
odd parent sums and zero otherwise. Unbiased stochastic rounding has expectation 0.

Selection-only comparison: a mathematical population with pair probabilities
proportional to the exact production fertility success threshold, versus uniform
pairs. Same 20 seeds/horizon/mutation/rounding. This isolates reproduction weighting
in a toy well-mixed model, not spatial pairing, survival or the whole ecological
algorithm. Other trait changes can reflect covariance, not direct selection.

Full unchanged ecology: fixed seeds [1,7,42,77,2026,4096], initially planned 10,000
ticks each. First benchmark one 1,000-tick pilot; report estimated campaign cost
before launching. Do not extend the horizon because a result is uninteresting.
Record founders/cohort/living traits, births, deaths, parent-depth and causes.
This short horizon cannot reproduce 428k ticks or establish historical attribution.
If budget requires shortening, declare the revision before running the campaign.
Stop on a determinism/accounting failure. No production variants or rule edits.
