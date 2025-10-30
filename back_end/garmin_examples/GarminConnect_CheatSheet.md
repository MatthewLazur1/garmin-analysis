# GarminConnect Python Library – Method Cheat Sheet

> A developer reference for commonly used functions in the `garminconnect` Python library (https://github.com/cyberjunky/python-garminconnect)

---

## 🧭 Authentication

| Method | Description |
|--------|-------------|
| `Garmin(email, password)` | Create a Garmin client instance |
| `login()` | Authenticate the user |
| `logout()` | End session and clear cookies |

---

## 📅 Activities & Metrics

| Method | Description |
|--------|-------------|
| `get_activities_by_date(start, end)` | Get activities within a date range |
| `get_all_activities(start, limit)` | Retrieve a paginated list of activities |
| `get_last_activity()` | Get the most recent activity |
| `get_activity(activity_id)` | Get basic metadata for a single activity |
| `get_activity_splits(activity_id)` | Get per-lap split data (duration, distance, HR) |
| `get_activity_details(activity_id)` | Detailed interval/lap data with workout context |
| `upload_activity_file(file)` | Upload a .fit/.gpx activity file |

---

## 🏃‍♀️ Health & Wellness Metrics

| Method | Description |
|--------|-------------|
| `get_body_battery()` | Body battery recovery/strain score |
| `get_resting_heart_rate()` | Daily RHR value |
| `get_training_readiness()` | Training readiness score |
| `get_sleep_data(date)` | Sleep summary for a given date |
| `get_stress_data(date)` | Stress score and breakdown |
| `get_respiration_data(date)` | Breathing rate info |
| `get_spo2_data(date)` | Blood oxygen saturation |
| `get_hrv_data(date)` | Heart Rate Variability |
| `get_hydration(date)` | Water intake summary |
| `add_hydration(amount, unit)` | Add water intake manually |
| `get_body_composition()` | Weight, body fat %, BMI, etc. |
| `add_body_composition(data)` | Add manual body metrics |

---

## 🧠 Training & Physiology

| Method | Description |
|--------|-------------|
| `get_training_status()` | Aerobic/anaerobic training effect |
| `get_race_predictions()` | Estimated 5K, 10K, HM, marathon times |
| `get_personal_records()` | All-time PRs for common distances |
| `get_max_metrics()` | VO2max, endurance, hill scores |
| `get_fitness_age()` | Garmin's estimate of your fitness age |

---

## ⚙️ Device, User & Settings

| Method | Description |
|--------|-------------|
| `get_user_profile()` | Basic user account info |
| `get_user_settings()` | Device preferences & privacy |
| `get_device_info()` | Linked Garmin device metadata |
| `get_device_alarms()` | Alarm clock settings on device |
| `get_gear()` | List shoes/bikes/etc. used in activities |

---

## 🏁 Goals, Challenges, & Badges

| Method | Description |
|--------|-------------|
| `get_active_goals()` | Ongoing fitness goals |
| `get_future_goals()` | Scheduled future goals |
| `get_past_goals()` | Archived or completed goals |
| `get_virtual_challenges()` | Joined challenges & leaderboard |
| `get_badge_challenges()` | Badges you're working toward |
| `get_ad_hoc_challenges()` | One-off or event-based challenges |

---

## 🔁 Misc / Utilities

| Method | Description |
|--------|-------------|
| `reload_epoch_data(date)` | Refresh local cache for given day |

---

## ✅ Example Usage

```python
from garminconnect import Garmin

client = Garmin("email@example.com", "password")
client.login()

activities = client.get_activities_by_date("2025-07-01", "2025-07-31")
splits = client.get_activity_splits(activities[0]["activityId"])
details = client.get_activity_details(activities[0]["activityId"])
```
