## Garmin Analysis

I’m an avid runner who has been training for marathons for several years. I’ve become deeply interested in the data behind running and how it can be used to improve performance. This project was created to support my running journey by providing both descriptive and predictive insights, helping me organize my training, and serving as a personal coaching platform all in one place.

To accomplish this, I built an end-to-end running analytics system featuring a clean, object-oriented backend, a Streamlit-based frontend, and integrations with APIs such as Garmin Connect and OpenWeatherMap for real-time data and insights.


---

## Highlights

- Predictive modeling for pace (min/mi) using personal Garmin data and weather context
- Object-oriented marathon plan engine (plan → weeks → runs) with JSON/CSV persistence
- Streamlit UI for weekly mileage, PRs, marathon planning, and one-click pace prediction
- API integrations: Garmin Connect (activities/sleep/HRV) and OpenWeatherMap (weather)

---

## Setup

- **Prerequisites:** 
    - Must have a Garmin watch with a Garmin Connect account.
    - Must have Open Weather Map API key. It is free to create and use on their website
- Requires Python version= >=3.13
- Environment variables (.env): 
    - GARMIN_EMAIL= ""
    - GARMIN_PASSWORD= "" 
    - OPENWEATHERMAP_API_KEY =

Quick start (from repo root):

```bash
uv sync
streamlit run front_end/app.py
```

For detailed usage of each tab (screenshots, tips), see `front_end/README.md`.

---

## Repository Structure

```text
garmin-analysis/
├── front_end/
│   ├── app.py                 # Streamlit application (tabs: Mileage, PRs, Marathon Plan, Pace)
│   └── README.md              # Feature-level usage and screenshots
├── back_end/
│   ├── constants.py           # HR targets, elevation heuristic, defaults
│   ├── marathon_objects/
│   │   └── marathon_plan_manager.py  # OOP plan model (MarathonPlan → PlanWeek → PlanRun)
│   ├── predictive_models/
│   │   ├── regression_predictive_model.py  # Ridge/LR model implementation
│   │   └── pca_predictive_model.py         # PCA + LR variant
│   └── report_objects/
│       ├── report_reader.py   # Garmin+Weather clients
│       ├── report_builder.py  # Feature engineering/aggregation utilities
│       └── report_manager.py  # Orchestration (training, loading plans, etc.)
└── plans/                     # Saved plans (JSON/CSV) [created at runtime]
```

---

## Features (Overview)

### 📊 Weekly Mileage
- Trend charts and summary metrics powered by Garmin activity data

### 🏆 Personal Records
- PR visualization and comparison (5K, 10K, HM, Marathon)

### 📝 Marathon Plan
- Create/load/save named plans
- Per-day fields: distance, type (Rest/Easy/Steady/Workout), notes
- Weekly totals and readable plan view

### ⚡ Predictive Pace
- One-click pace prediction for today’s planned run
- Inputs: plan (distance/type), Garmin sleep/HRV/resting HR, weather (temp/humidity)
- Output: predicted pace (min/mi) with key metrics

For how to use each tab, see `front_end/README.md`.

---

## Modeling Notes (Brief)

- Explored Linear Regression, Ridge Regression (α tuning), and PCA + LR
- Optimized for practical accuracy within ±10–15 seconds rather than R²
- Current best: Ridge Regression (α = 5)
- Data since Jan 1, 2024 from Garmin and OpenWeatherMap

See the model report in `back_end/predictive_models/model_tuning.md` for full context and results.

---

## What’s Next

- Marathon Plan: cleaner aesthetics, richer editing features
- Pace Model: improved accuracy, richer route/elevation and weather factors
- AI Marathon Planner/Coach integrated directly into the Plan tab
- More health metrics surfaced on the landing tab (HRV/RHR/sleep insights)

---

## License & Credits

- Built with Streamlit, pandas, scikit-learn, and garminconnect
- Weather via OpenWeatherMap
- License: TODO (MIT/Apache-2.0)