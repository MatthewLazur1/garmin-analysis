import os
import json
from datetime import date, datetime
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd

from report_objects.report_builder import ReportBuilder
from back_end.marathon_objects.marathon_plan_manager import MarathonPlan
from report_objects.report_reader import ReportReader
from back_end.predictive_models.regression_predictive_model import PredictivePacingModel
from back_end.predictive_models.pca_predictive_model import PredictivePacingModelPCA
from constants import (
    REGRESSION_START_DATE_YEAR,
    REGRESSION_START_DATE_MONTH,
    REGRESSION_START_DATE_DAY,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    ELEVATION_FT_PER_MILE,
    HR_TARGETS,
)

class ReportManager:
    def __init__(self):
        self.report_builder = ReportBuilder()
        self.report_reader = ReportReader()
        self.marathon_plans = {}
        # Project root for plan files (JSON/CSV stored at repo root)
        self._root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self._plans_dir = os.path.join(self._root, 'plans')
        # Predictive model holder
        self.pacing_model: Optional[PredictivePacingModel] = None
        self.pacing_model_pca: Optional[PredictivePacingModelPCA] = None

    def get_activity_statistics(self, client, start_date, end_date, week_period_days=7):
        """
        Build a combined statistics dictionary for the given date range.

        Returns a dict with:
        - 'weekly_mileage': DataFrame with weekly mileage aggregates
        - 'personal_records': DataFrame with all-time personal records
        """
        weekly_mileage = self.report_builder.aggregate_weekly_mileage(
            client=client,
            start_date=start_date,
            end_date=end_date,
            time_delta=week_period_days,
        )

        personal_records = self.report_builder.get_all_time_prs(client)

        return {
            'weekly_mileage': weekly_mileage,
            'personal_records': personal_records,
        }
    
    def get_activity_data(self, client, activity_id):
        activity_summary = self.report_builder.get_activity_summary(client, activity_id)
        weather_data = self.report_builder.get_activity_weather(activity_summary)
        activity_summary_weather = activity_summary.merge(weather_data, on=['activity_id'], how='left')
        sleep_data = self.report_builder.get_sleep_data(activity_summary_weather, client)
        activity_summary_weather_sleep = activity_summary_weather.merge(sleep_data, on=['activity_id'], how='left')
        days_since_start = self.report_builder.get_days_since_start(activity_summary_weather_sleep)
        activity_summary_weather_sleep_days = activity_summary_weather_sleep.merge(days_since_start, on=['activity_id'], how='left')
        return activity_summary_weather_sleep_days
    
    def get_regression_data(self, client):
        print("Getting regression data")
        today = date.today()
        start_date = date(REGRESSION_START_DATE_YEAR, REGRESSION_START_DATE_MONTH, REGRESSION_START_DATE_DAY)
       
        activity_data = client.get_activities_by_date(start_date.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'))
        regression_data = pd.DataFrame()
        
        for activity in activity_data:
            activity_type = activity.get('activityType', {}).get('typeKey', '').lower()
            # Only include running activities
            if activity_type in ['running']:
                activity_id = activity['activityId']
                activity_data = self.get_activity_data(client, activity_id)
                regression_data = pd.concat([regression_data, activity_data], ignore_index=True)
        regression_data = regression_data.drop(columns=['activity_id', 'activity_name', 'start_time', 'finish_time', 'longitude', 'latitude'])
        return regression_data

    # -------- Predictive Pacing Model --------
    def train_pacing_model(self, client) -> Dict[str, Any]:
        """
        Build regression dataset, train the pacing model, analyze, and store it.
        Returns basic metrics for display.
        """
        df = self.get_regression_data(client)
        model = PredictivePacingModel()
        model.train_model(df)
        metrics: Dict[str, Any] = {}
        try:
            vif, accuracy, coef_df, r_squared_train, r_squared_test = model.analyze_model()
            metrics = {
                'accuracy_within_10s_percent': accuracy,
                'r_squared_train': r_squared_train,
                'r_squared_test': r_squared_test,
                'coefficients': coef_df.to_dict(orient='records'),
            }
        except Exception:
            metrics = {}
        self.pacing_model = model
        return metrics

    def predict_pace(self, current_data: Dict[str, Any]) -> float:
        if self.pacing_model is None:
            raise RuntimeError("Pacing model not trained. Call train_pacing_model(client) first.")
        return float(self.pacing_model.predict_pace(current_data))

    def predict_plan_day_pace(self, client, df_plan: pd.DataFrame, week: int, day_name: str) -> Optional[Dict[str, Any]]:
        """
        Build inputs for a specific day in the plan and return inputs + prediction.
        Skips if Rest or missing critical data.
        """
        print("Predicting plan day pace")
        print("DF Plan: ", df_plan)
        print("Week: ", week)
        print("Day Name: ", day_name)
        if day_name not in MarathonPlan.DAY_COLUMNS:
            return None
        row = df_plan.loc[df_plan['Week'] == week]
        if row.empty:
            return None
        row = row.iloc[0]
        try:
            dist = float(row.get(f"{day_name}_Dist", 0.0) or 0.0)
            print("Dist: ", dist)
        except Exception:
            dist = 0.0
        rtype = str(row.get(f"{day_name}_Type", '') or '')
        print("RType: ", rtype)
        if rtype == 'Rest' or dist <= 0:
            return None
        avg_hr = HR_TARGETS.get(rtype)
        print("Avg HR: ", avg_hr)
        if avg_hr is None:
            return None
        try:
            start_monday = datetime.strptime(row['First_Monday'], '%Y-%m-%d').date()
        except Exception:
            return None
        day_index = MarathonPlan.DAY_COLUMNS.index(day_name)
        run_date = start_monday + pd.Timedelta(days=day_index)
        print("Run Date: ", run_date)
        # Features
        distance_miles = dist
        elevation_gain = distance_miles * ELEVATION_FT_PER_MILE
        print("Elevation Gain: ", elevation_gain)
        # Weather (current-style reading for that day)
        try:
            weather_item = self.report_reader.fetch_weather_data_openweathermap(
                DEFAULT_LATITUDE, DEFAULT_LONGITUDE, pd.Timestamp(run_date), pd.Timestamp(run_date)
            )
            item = weather_item[0] if isinstance(weather_item, list) else weather_item
            main = item.get('main', {}) if isinstance(item, dict) else {}
            temperature = main.get('temp')
            humidity = main.get('humidity')
            print("Temperature: ", temperature)
            print("Humidity: ", humidity)
        except Exception:
            return None
        # Sleep (previous night)
        try:
            sleep_date_str = (pd.Timestamp(run_date)).strftime('%Y-%m-%d')
            sleep_data = client.get_sleep_data(sleep_date_str)
            hrv_data = client.get_hrv_data(sleep_date_str)
            hrv = hrv_data['hrvSummary']['lastNightAvg']
            resting_heart_rate = sleep_data.get('restingHeartRate')
            print("HRV: ", hrv)
            print("Resting Heart Rate: ", resting_heart_rate)
        except Exception:
            return None
        # Days since start
        start_date = date(REGRESSION_START_DATE_YEAR, REGRESSION_START_DATE_MONTH, REGRESSION_START_DATE_DAY)
        days_since_start = (pd.Timestamp(run_date).date() - start_date).days
        required = [distance_miles, avg_hr, temperature, hrv, days_since_start, elevation_gain, resting_heart_rate, humidity]
        print("Required: ", required)
        if any(x is None for x in required):
            return None
        if self.pacing_model is None:
            self.train_pacing_model(client)
        features = {
            'distance_miles': float(distance_miles),
            'avg_hr': float(avg_hr),
            'temperature': float(temperature),
            'hrv': float(hrv),
            'days_since_start': float(days_since_start),
            'elevation_gain': float(elevation_gain),
            'resting_heart_rate': float(resting_heart_rate),
            'humidity': float(humidity),
        }
        pace = self.predict_pace(features)
        return {
            'inputs': features,
            'week': int(week),
            'day': day_name,
            'run_date': str(pd.Timestamp(run_date).date()),
            'type': rtype,
            'predicted_pace_min_per_mile': round(float(pace), 2),
            'temperature': float(temperature),
            'humidity': float(humidity),
            'hrv': float(hrv),
            'resting_heart_rate': float(resting_heart_rate),
        }

    # -------- Marathon Plan Management (multi-plan) --------
    def list_plans(self) -> List[str]:
        # Return names based on *.json files at root (filename stem)
        try:
            os.makedirs(self._plans_dir, exist_ok=True)
            files = os.listdir(self._plans_dir)
        except Exception:
            return []
        names: List[str] = []
        for f in files:
            if f.lower().endswith('.json'):
                name = os.path.splitext(f)[0]
                names.append(name)
        # include in-memory plans that may not be on disk yet
        names.extend([n for n in self.marathon_plans.keys() if n not in names])
        return sorted(names)

    def load_plan(self, name: Optional[str] = None) -> Optional[Tuple[str, date, date, pd.DataFrame]]:
        if name is None:
            names = self.list_plans()
            if not names:
                return None
            name = names[0]
        if name in self.marathon_plans:
            plan_obj: MarathonPlan = self.marathon_plans[name]
        else:
            os.makedirs(self._plans_dir, exist_ok=True)
            json_path = os.path.join(self._plans_dir, f"{name}.json")
            csv_path = os.path.join(self._plans_dir, f"{name}.csv")
            if not os.path.exists(json_path) or not os.path.exists(csv_path):
                return None
            try:
                plan_obj = MarathonPlan.load_from_disk(name, self._plans_dir)
            except Exception:
                return None
            self.marathon_plans[name] = plan_obj
        marathon_name, start, end, df = plan_obj.get_plan()
        if isinstance(start, datetime):
            start = start.date()
        if isinstance(end, datetime):
            end = end.date()
        return marathon_name, start, end, df

    def save_plan(self, name: str, start: date, race: date, df: pd.DataFrame) -> None:
        if name not in self.marathon_plans:
            self.marathon_plans[name] = MarathonPlan(name, start, race)
        plan_obj: MarathonPlan = self.marathon_plans[name]
        plan_obj.name = name
        plan_obj.start = start
        plan_obj.end = race
        plan_obj.from_dataframe(df.copy())
        plan_obj.df = plan_obj.to_dataframe()
        plan_obj.save_to_disk(self._plans_dir)
        

    # Legacy helpers removed; persistence centralized in MarathonPlan