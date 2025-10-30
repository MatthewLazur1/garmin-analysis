## Predictive Pace Model

### Overview
This document summarizes the modeling approaches I explored to predict running pace (min/mi) from Garmin and weather signals. It’s written f to quickly show my end-to-end ML workflow, decision-making, and the rationale behind the final model choice. The focus is on practical prediction accuracy (±10–15s) rather than purely academic metrics.

### Problem Statement
Predict a runner’s expected pace for a planned run using recent personal data (Garmin) and contextual conditions (OpenWeatherMap). The goal is a reliable, personalized estimate that helps guide training and race preparation.

### Data
- Source and range:
  - Garmin activity + wellness data and OpenWeatherMap weather data
  - Time range: Jan 1, 2024 → present
- Features (evolving set during experimentation):
  - distance_miles
  - avg_hr (targeted HR for the planned run)
  - temperature (°F)
  - humidity (%)
  - hrv (ms; previous night)
  - resting_heart_rate (bpm; previous night)
  - days_since_start (based on constants.py start date)
  - elevation_gain (ft; currently set as 50 ft/mile)
- Current constants (subject to change):
  - HR targets per run type in `constants.py`
  - Elevation gain assumption: 50 ft/mile
  - Default weather location: Raleigh, NC

### Why Pace Prediction Is Hard
- High intra- and inter-run variability (terrain, fatigue, interruptions, sleep, heat, fueling).
- Workouts include intervals/rest periods → volatile HR and effort signals.
- Easy runs are comparatively predictable (steady-state effort).
- Data scarcity: personalization needs per-athlete history; expanding data is non-trivial.

### Evaluation
- Primary metric: accuracy within a narrow tolerance of the real-world target.
  - I emphasized classification-like “closeness”: % of predictions within ±10–15 seconds of actual pace.
  - R² was monitored but explicitly not the optimization objective for model selection.
- Data hygiene:
  - Dropped rows with missing or non-finite values in training features and target.
  - Guarded against leakage by using proper train/test separation where applicable.

### Models Explored and Rationale
- Linear Regression (LR)
  - Why: Fast baseline; interpretable; establishes a standard for subsequent models.
  - What I checked:
    - VIF early on to gauge multicollinearity (when not using PCA)
    - Accuracy within ±10–15 seconds
  - Outcome: Strong baseline; helped identify the most predictive features.

- Ridge Regression (L2)
  - Why: Manage multicollinearity while maintaining all features; shrinks noisy coefficients.
  - What I tuned: Alpha (regularization strength); selected for best ±10–15s accuracy.
  - Outcome: Best practical performance; ultimately chosen as the final model with alpha=5.

- PCA + Linear Regression
  - Why: De-correlate inputs, potentially improve generalization on limited data.
  - What I tuned: Number of components (or % variance explained).
  - Outcome: Competitive and stable; informative for understanding structure in features, but did not surpass Ridge in the primary accuracy metric.

### Final Model
- Selected: Ridge Regression (alpha = 5)
- Selection criteria: Highest accuracy within ±10–15s tolerance across test splits and consistent behavior across runs.

### Results Summary
- Headline: Ridge (α=5) produced the most reliable accuracy in the ±10–15s band across my test splits, outperforming the plain LR and PCA+LR variants on the primary objective.
- Supporting observations:
  - Easy runs yielded the tightest errors due to steady-state effort.
  - Workouts showed higher variance and lower hit-rate within ±10–15s due to interval/rest structure and acute fatigue variability.

### Modeling Decisions and Trade-offs
- Optimized for practical closeness (±10–15s) over R² because prediction usefulness is defined by actionable error bounds, not variance explanation.
- Chose Ridge over PCA+LR for operational simplicity (no extra transform step) and slightly better tolerance accuracy.
- Retained interpretable, controllable features (HR targets by run type, days since start, elevation heuristic) with the intention to improve these with more precise data later.

### Limitations
- Elevation is approximations (heuristic 50 ft/mile). This should be replaced by route-level elevation.
- Sleep and HR-based signals are personal and noisy; more coverage improves stability.
- Workouts are inherently harder; sub-models by run type (Workout vs. Easy/Steady) may further improve accuracy.

### Next Steps
- Replace elevation heuristic with route elevation profiles.
- Explore more health, environment, and activity variable that better predict pace.
- Explore modern, more accurate predictive models.

### Repro/Usage Notes
- Dependencies: see project’s requirements and `constants.py` for current defaults (HR targets, elevation assumption, default lat/lon).
- Data access:
  - Garmin Connect via authenticated client (tokens or credentials).
  - OpenWeatherMap (API key required).
- Training/evaluation:
  - Prepare data using repository utilities, then train Ridge with α=5 (as configured in code).
  - Evaluate with the ±10–15s accuracy metric; monitor R² secondarily.

### Key Takeaways
- Ridge Regression with α=5 gave the best practical accuracy for personalized pace prediction under tight tolerances.
- Data quality and context matter more than algorithm complexity; steady-state easy runs are more predictable than structured workouts.
- The pipeline is designed to evolve: constants and signals will be refined as I add enhance variables and the predictive model type.
