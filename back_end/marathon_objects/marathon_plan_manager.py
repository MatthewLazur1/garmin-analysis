import os
import json
import re
from datetime import date, datetime, timedelta
from typing import Optional, Tuple, Dict, Any, List
from typing import Tuple

import pandas as pd
from back_end.report_objects.report_reader import ReportReader
from back_end.constants import (
    REGRESSION_START_DATE_YEAR,
    REGRESSION_START_DATE_MONTH,
    REGRESSION_START_DATE_DAY,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    ELEVATION_FT_PER_MILE,
    HR_TARGETS,
)
from back_end.predictive_models.regression_predictive_model import PredictivePacingModel


class PlanRun:
    """
    Represents a single planned run.

    Attributes:
        date: The calendar date of the run (datetime.date)
        distance: Planned distance in miles (float)
        run_type: One of the supported run types (str)
        notes: Free-form notes (str)
    """

    def __init__(self, date: date, distance: float = 0.0, run_type: str = 'Rest', notes: str = ''):
        self._date = date
        self._distance = float(distance) if distance is not None else 0.0
        self._type = str(run_type) if run_type is not None else 'Rest'
        self._notes = str(notes) if notes is not None else ''

    # Getters
    def get_distance(self) -> float:
        return self._distance

    def get_type(self) -> str:
        return self._type

    def get_notes(self) -> str:
        return self._notes

    def get_date(self) -> date:
        return self._date

    # Setters
    def set_distance(self, distance: float) -> None:
        self._distance = float(distance) if distance is not None else 0.0

    def set_type(self, run_type: str) -> None:
        self._type = str(run_type) if run_type is not None else 'Rest'

    def set_notes(self, notes: str) -> None:
        self._notes = str(notes) if notes is not None else ''


class PlanWeek:
    """
    Represents one training week composed of 7 PlanRun entries.
    Week boundaries are derived from the plan's Monday-aligned start date.
    """

    def __init__(self, week_number: int, plan_start_monday: date, run_types: list[str], runs_by_day: dict | None = None):
        self.week_number = int(week_number)
        # Week start/end computed from the plan start Monday
        self.start_date: date = plan_start_monday + timedelta(days=7 * (self.week_number - 1))
        self.end_date: date = self.start_date + timedelta(days=6)
        self._day_names = MarathonPlan.DAY_COLUMNS
        self._runs: dict[str, PlanRun] = {}

        if runs_by_day is not None:
            # Expect mapping of day name -> PlanRun
            for day in self._day_names:
                self._runs[day] = runs_by_day.get(day) or PlanRun(self._day_date(day), 0.0, run_types[0], '')
        else:
            for day in self._day_names:
                self._runs[day] = PlanRun(self._day_date(day), 0.0, run_types[0], '')

    def _day_date(self, day_name: str) -> date:
        idx = self._day_names.index(day_name)
        return self.start_date + timedelta(days=idx)

    def get_run(self, day_name: str) -> PlanRun:
        return self._runs[day_name]

    def set_run(self, day_name: str, run: PlanRun) -> None:
        self._runs[day_name] = run

    def weekly_total(self) -> float:
        return round(sum(self._runs[day].get_distance() for day in self._day_names), 2)

    def to_row(self) -> dict:
        """Serialize week to a DataFrame row using Dist/Type/Notes schema."""
        row: dict[str, Any] = {
            'Week': self.week_number,
            'First_Monday': self.start_date.strftime('%Y-%m-%d'),
        }
        for day in self._day_names:
            run = self._runs[day]
            row[f"{day}_Dist"] = run.get_distance()
            row[f"{day}_Type"] = run.get_type()
            row[f"{day}_Notes"] = run.get_notes()
        return row

    @classmethod
    def from_row(cls, row: pd.Series, plan_start_monday: date, run_types: list[str]) -> 'PlanWeek':
        week_number = int(row['Week'])
        week = cls(week_number, plan_start_monday, run_types)
        for day in MarathonPlan.DAY_COLUMNS:
            rdate = week._day_date(day)
            dist = row.get(f"{day}_Dist", 0.0)
            rtype = row.get(f"{day}_Type", run_types[0])
            notes = row.get(f"{day}_Notes", '')
            try:
                dist = float(dist) if dist is not None else 0.0
            except Exception:
                dist = 0.0
            week.set_run(day, PlanRun(rdate, dist, str(rtype), str(notes)))
        return week


class MarathonPlan:
    """
    Single-plan helper: generate a plan, compute weekly totals, and parse day miles.

    Plan format (DataFrame):
    - Raw Columns: 'Week', 'First_Monday', 'Mon','Tue','Wed','Thu','Fri','Sat','Sun'
    - Day cells are free text, recommended format "<miles>: Description" (e.g., "8: Easy")
    - 'Weekly Total' is a computed-only column for display; it is not stored in the raw plan
    """

    DAY_COLUMNS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    RUN_TYPES = ['Rest', 'Easy', 'Steady', 'Workout']
    META_KEYS = ['name', 'start_date', 'race_date']

    def __init__(self, name: str, start: date, end: date):
        self.name = name
        self.start = start
        self.end = end
        # Object model
        self.weeks: list[PlanWeek] = []
        # Initialize with generated plan (and keep df in sync for compatibility)
        self.df = self.generate_plan(name, start, end)

    # ---------- Public API ----------
    def _dist_col(self, day: str) -> str:
        return f"{day}_Dist"

    def _type_col(self, day: str) -> str:
        return f"{day}_Type"

    def _notes_col(self, day: str) -> str:
        return f"{day}_Notes"

    @classmethod
    def distance_columns(cls) -> List[str]:
        return [f"{day}_Dist" for day in cls.DAY_COLUMNS]

    @classmethod
    def type_columns(cls) -> List[str]:
        return [f"{day}_Type" for day in cls.DAY_COLUMNS]

    @classmethod
    def notes_columns(cls) -> List[str]:
        return [f"{day}_Notes" for day in cls.DAY_COLUMNS]

    def generate_plan(self, name: str, start: date, end: date) -> pd.DataFrame:
        """
        Build a weekly plan from the week containing 'start' through the week containing 'end'.
        Returns a RAW DataFrame ready for editing in the UI (no 'Weekly Total' column).
        """
        if not isinstance(start, (date, datetime)) or not isinstance(end, (date, datetime)):
            raise TypeError('start and end must be date or datetime')

        start_d = start.date() if isinstance(start, datetime) else start
        end_d = end.date() if isinstance(end, datetime) else end

        # Monday of the start week and Monday of the race week
        start_monday = start_d - timedelta(days=start_d.weekday())
        end_monday = end_d - timedelta(days=end_d.weekday())

        # Build weekly rows from start_monday through end_monday inclusive
        week_starts = []
        current = start_monday
        while current <= end_monday:
            week_starts.append(current)
            current += timedelta(days=7)

        # Build weeks object list
        self.weeks = []
        for idx, monday in enumerate(week_starts, start=1):
            self.weeks.append(PlanWeek(idx, start_monday, self.RUN_TYPES))
        # Produce DataFrame view
        df_rows = [w.to_row() for w in self.weeks]
        df = pd.DataFrame(df_rows, columns=['Week', 'First_Monday', *self.distance_columns(), *self.type_columns(), *self.notes_columns()])
        return df

    def compute_weekly_totals(self) -> pd.DataFrame:
        # Ensure df is synchronized with weeks
        self.df = self.to_dataframe()
        dist_cols = self.distance_columns()
        self.df['Weekly Total'] = self.df[dist_cols].sum(axis=1).round(2)
        return self.df

    @classmethod
    def compute_weekly_totals_df(cls, df: pd.DataFrame) -> pd.DataFrame:
        copy_df = df.copy()
        dist_cols = cls.distance_columns()
        for col in dist_cols:
            if col not in copy_df.columns:
                copy_df[col] = 0.0
        copy_df['Weekly Total'] = copy_df[dist_cols].sum(axis=1).round(2)
        return copy_df

    @classmethod
    def build_readable_view(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Return a display DataFrame with columns: Week, First_Monday, Mon..Sun (combined string), Weekly Total
        Combined string per day: "<dist> <type> - <notes>" if dist>0; "Rest - <notes>" if type==Rest and dist==0; notes optional.
        """
        source = cls.compute_weekly_totals_df(df)
        display_rows: List[Dict[str, Any]] = []
        for _, row in source.iterrows():
            out: Dict[str, Any] = {
                'Week': row['Week'],
                'First_Monday': row['First_Monday'],
            }
            for day in cls.DAY_COLUMNS:
                dist = row.get(f"{day}_Dist", 0.0)
                rtype = row.get(f"{day}_Type", '')
                notes = row.get(f"{day}_Notes", '')
                parts: List[str] = []
                if (isinstance(dist, (int, float)) and float(dist) > 0) or (isinstance(dist, str) and dist.strip()):
                    try:
                        dval = float(dist)
                    except Exception:
                        dval = 0.0
                    if dval > 0:
                        parts.append(f"{dval:g}")
                if rtype:
                    parts.append(str(rtype))
                if notes:
                    parts.append(str(notes))
                if not parts:
                    parts.append('')
                out[day] = ' - '.join(parts) if len(parts) > 2 else ' '.join(parts)
            out['Weekly Total'] = row.get('Weekly Total', 0.0)
            display_rows.append(out)
        return pd.DataFrame(display_rows, columns=['Week', 'First_Monday', *cls.DAY_COLUMNS, 'Weekly Total'])


    def get_plan(self) -> Tuple[str, date, date, pd.DataFrame]:
        # Always return a fresh DataFrame view
        return self.name, self.start, self.end, self.to_dataframe()
    
    def save_plan(self) -> None:
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        plans_dir = os.path.join(root, 'plans')
        os.makedirs(plans_dir, exist_ok=True)
        csv_path = os.path.join(plans_dir, f"{self.name}.csv")
        self.to_dataframe().to_csv(csv_path, index=False)
        json_path = os.path.join(plans_dir, f"{self.name}.json")
        metadata = {
            'name': self.name,
            'start_date': self.start.isoformat(), # Convert date objects to strings
            'race_date': self.end.isoformat()
        }
        with open(json_path, 'w') as f:
            json.dump(metadata, f)

    def load_plan(self) -> None:
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        plans_dir = os.path.join(root, 'plans')
        json_path = os.path.join(plans_dir, f"{self.name}.json")
        with open(json_path, 'r') as f:
            metadata = json.load(f)
            self.name = metadata['name']
            self.start = datetime.fromisoformat(metadata['start_date'])
            self.end = datetime.fromisoformat(metadata['race_date'])
            csv_path = os.path.join(plans_dir, f"{self.name}.csv")
            df = pd.read_csv(csv_path)
            # Rebuild object model from DataFrame
            self.from_dataframe(df)
            self.df = self.to_dataframe()

    # Centralized persistence helpers
    def save_to_disk(self, plans_dir: str) -> None:
        os.makedirs(plans_dir, exist_ok=True)
        csv_path = os.path.join(plans_dir, f"{self.name}.csv")
        self.to_dataframe().to_csv(csv_path, index=False)
        json_path = os.path.join(plans_dir, f"{self.name}.json")
        with open(json_path, 'w') as f:
            json.dump({
                'name': self.name,
                'start_date': self.start.isoformat(),
                'race_date': self.end.isoformat(),
            }, f)

    @classmethod
    def load_from_disk(cls, name: str, plans_dir: str) -> 'MarathonPlan':
        json_path = os.path.join(plans_dir, f"{name}.json")
        csv_path = os.path.join(plans_dir, f"{name}.csv")
        with open(json_path, 'r') as f:
            metadata = json.load(f)
        start = datetime.fromisoformat(metadata['start_date']).date()
        end = datetime.fromisoformat(metadata['race_date']).date()
        df = pd.read_csv(csv_path)
        plan = cls(name, start, end)
        plan.from_dataframe(df)
        plan.df = plan.to_dataframe()
        return plan
        

    # No persistence here; storage is handled by ReportManager

    # ---------- Internal helpers ----------


    def _to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'start_date': self.start.strftime('%Y-%m-%d'),
            'end_date': self.end.strftime('%Y-%m-%d'),
            'df': self.df
        }

    # ---------- Object/DataFrame conversion ----------
    def to_dataframe(self) -> pd.DataFrame:
        """Serialize the current weeks to the editor-friendly DataFrame schema."""
        if not self.weeks:
            return self.df.copy() if isinstance(self.df, pd.DataFrame) else pd.DataFrame()
        rows = [w.to_row() for w in self.weeks]
        return pd.DataFrame(rows, columns=['Week', 'First_Monday', *self.distance_columns(), *self.type_columns(), *self.notes_columns()])

    def from_dataframe(self, df: pd.DataFrame) -> None:
        """Populate weeks from a DataFrame produced by the editor."""
        if df is None or df.empty:
            self.weeks = []
            return
        # Plan start Monday is the Monday of self.start
        plan_start_monday = (self.start - timedelta(days=self.start.weekday())) if isinstance(self.start, date) else datetime.strptime(str(self.start), '%Y-%m-%d').date()
        self.weeks = []
        for _, row in df.iterrows():
            week = PlanWeek.from_row(row, plan_start_monday, self.RUN_TYPES)
            self.weeks.append(week)

    # ---------- Prediction helpers ----------
    def _find_week_and_day_by_date(self, run_date: date) -> Optional[Tuple[PlanWeek, str, PlanRun]]:
        if not self.weeks:
            # Try to build weeks from df if present
            if isinstance(self.df, pd.DataFrame) and not self.df.empty:
                self.from_dataframe(self.df)
        for week in self.weeks:
            if week.start_date <= run_date <= week.end_date:
                day_idx = (run_date - week.start_date).days
                if 0 <= day_idx < len(self.DAY_COLUMNS):
                    day_name = self.DAY_COLUMNS[day_idx]
                    run = week.get_run(day_name)
                    return week, day_name, run
        return None

    def predict_pace_for_run_date(
        self,
        client,
        run_date: date,
        model: Optional[PredictivePacingModel] = None,
        reader: Optional[ReportReader] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Predict pace for the run on a given date using the object model.
        Returns inputs and prediction; skips Rest/zero distance/missing data.
        """
        found = self._find_week_and_day_by_date(run_date)
        if not found:
            return None
        _, day_name, run = found

        dist = float(run.get_distance() or 0.0)
        rtype = str(run.get_type() or '')
        if rtype == 'Rest' or dist <= 0:
            return None
        avg_hr = HR_TARGETS.get(rtype)
        if avg_hr is None:
            return None

        # Weather at current time on run_date
        if reader is None:
            reader = ReportReader()
        # Use current local time merged into run_date
        now_local = datetime.now()
        run_dt = datetime.combine(run_date, now_local.time())
        try:
            weather_item = reader.fetch_weather_data_openweathermap(
                DEFAULT_LATITUDE, DEFAULT_LONGITUDE, pd.Timestamp(run_dt), pd.Timestamp(run_dt)
            )
            item = weather_item[0] if isinstance(weather_item, list) else weather_item
            main = item.get('main', {}) if isinstance(item, dict) else {}
            temperature = main.get('temp')
            humidity = main.get('humidity')
        except Exception:
            return None

        # Sleep for previous night of run_date
        try:
            sleep_date_str = (pd.Timestamp(run_date)).strftime('%Y-%m-%d')
            sleep_data = client.get_sleep_data(sleep_date_str)
            hrv_data = client.get_hrv_data(sleep_date_str)
            hrv = hrv_data['hrvSummary']['lastNightAvg']
            resting_heart_rate = sleep_data.get('restingHeartRate')
        except Exception:
            return None

        # Derived features
        distance_miles = dist
        elevation_gain = distance_miles * ELEVATION_FT_PER_MILE
        start_date0 = date(REGRESSION_START_DATE_YEAR, REGRESSION_START_DATE_MONTH, REGRESSION_START_DATE_DAY)
        days_since_start = (pd.Timestamp(run_date).date() - start_date0).days

        required = [distance_miles, avg_hr, temperature, hrv, days_since_start, elevation_gain, resting_heart_rate, humidity]
        if any(x is None for x in required):
            return None

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

        result: Dict[str, Any] = {
            'inputs': features,
            'run_date': run_date.strftime('%Y-%m-%d'),
            'type': rtype,
            'temperature': float(temperature),
            'humidity': float(humidity),
            'hrv': float(hrv),
            'resting_heart_rate': float(resting_heart_rate),
        }

        if model is None:
            return None
        pace = float(model.predict_pace(features))
        result['predicted_pace_min_per_mile'] = round(pace, 2)
        return result


