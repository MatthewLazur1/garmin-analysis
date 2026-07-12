import pandas as pd
from datetime import datetime, timedelta, date
import json
from back_end.report_objects.report_reader import ReportReader
from back_end.constants import REGRESSION_START_DATE_YEAR, REGRESSION_START_DATE_MONTH, REGRESSION_START_DATE_DAY

class ReportBuilder:
    def __init__(self):
        self.report = {}
        self.report_reader = ReportReader()
    
    def aggregate_weekly_mileage(self, client, start_date, end_date, time_delta=7):
        """
        Aggregate weekly mileage for running activities between start_date and end_date.
        
        Args:
            client: Garmin client instance
            start_date: Start date (datetime or date object)
            end_date: End date (datetime or date object)
            time_delta: Number of days for each week (default: 7)
        
        Returns:
            DataFrame with weekly mileage totals
        """
        # Normalize inputs to datetime for internal use
        if isinstance(start_date, str):
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        elif isinstance(start_date, datetime):
            start_dt = start_date
        elif isinstance(start_date, date):
            start_dt = datetime.combine(start_date, datetime.min.time())
        else:
            raise TypeError("start_date must be a datetime, date, or 'YYYY-MM-DD' string")

        if isinstance(end_date, str):
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        elif isinstance(end_date, datetime):
            end_dt = end_date
        elif isinstance(end_date, date):
            end_dt = datetime.combine(end_date, datetime.min.time())
        else:
            raise TypeError("end_date must be a datetime, date, or 'YYYY-MM-DD' string")

        # Garmin API expects date strings in 'YYYY-MM-DD'
        api_start = start_dt.strftime('%Y-%m-%d')
        api_end = end_dt.strftime('%Y-%m-%d')

        # Get activities for the date range
        activities = client.get_activities_by_date(api_start, api_end)
        # with open('activities.json', 'w') as f:
        #     json.dump(activities, f, indent=4)
        # Filter for running activities
        running_activities = []
        for activity in activities:
            activity_type = activity.get('activityType', {}).get('typeKey', '').lower()
            if activity_type in ['treadmill_running', 'running', 'manual', 'track_running']:
                running_activities.append(activity)
        
        # Convert to DataFrame
        df = pd.DataFrame(running_activities)
        
        if df.empty:
            print("No running activities found in the specified date range.")
            return pd.DataFrame()
        
        # Convert distance from meters to miles
        df['distance_miles'] = df['distance'] / 1609.34
        
        # Convert start time to datetime
        df['start_time'] = pd.to_datetime(df['startTimeLocal'])
        
        # Create proper weekly periods (Monday to Sunday)
        df['week_start'] = df['start_time'].dt.to_period('W-SUN')  # Week starting Sunday
        
        # Group by week and sum distances
        weekly_mileage = df.groupby('week_start')['distance_miles'].agg([
            'sum',  # Total mileage
            'count',  # Number of activities
        ]).round(2)
        
        # Rename columns for clarity
        weekly_mileage.columns = ['Total_Miles', 'Activity_Count',]
        
        # Convert period index to show week range more clearly
        # weekly_mileage.index = [f"{period.start_time.strftime('%Y-%m-%d')} to {period.end_time.strftime('%Y-%m-%d')}" 
        #                        for period in weekly_mileage.index]
        
        # Alternative: Show just the week start date for cleaner display
        weekly_mileage.index = [f"Week of {period.start_time.strftime('%Y-%m-%d')}" 
                               for period in weekly_mileage.index]
        weekly_mileage.index.name = 'week_start'
        
        return weekly_mileage
    
    def get_all_time_prs(self, client):
        """
            Returns all time personal records for the user
        """
        pr_data = client.get_personal_record()
        DISTANCE_MAP = {
        3: {'distance': 3.10686, 'name': '5K'},
        4: {'distance': 6.21371, 'name': '10K'},
        5: {'distance': 13.1094, 'name': 'Half Marathon'},
        6: {'distance': 26.2188, 'name': 'Marathon'},
    }
    
        records = []
        for record in pr_data:
            type_id = record['typeId']
            dist_info = DISTANCE_MAP.get(type_id)
            if dist_info is None:
                continue
            if record['value'] > 0:
                # Calculate pace in min/mile (meters to miles conversion)
                pace_min_per_mile = (record['value'] / 60) / (dist_info['distance'])
                
                # Format time as HH:MM:SS
                total_seconds = record['value']
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                seconds = int(total_seconds % 60)
                formatted_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                
                # Format pace as X:YY/mile
                pace_min = int(pace_min_per_mile)
                pace_sec = int((pace_min_per_mile % 1) * 60)
                formatted_pace = f"{pace_min}:{pace_sec:02d}/mile"
                
                records.append({
                    'Distance': dist_info['name'],
                    'Time': formatted_time,
                    'Pace': formatted_pace,
                    # Keep raw numbers for sorting/analysis
                    '_seconds': total_seconds,
                    '_pace_value': pace_min_per_mile
                })
        
        # Create DataFrame and sort by distance
        df = pd.DataFrame(records)
        df = df.sort_values('_seconds').reset_index(drop=True)
        
        return df[['Distance', 'Time', 'Pace']]
        

        
    
    def show_activity_splits(self, activity_id, client):
        details = client.get_activity_splits(activity_id)

        laps = details["lapDTOs"]

        # Print summary for each lap
        for lap in laps:
            dist_mi = lap["distance"] / 1609.34
            pace_sec_per_mile = lap["duration"] / dist_mi if dist_mi > 0 else 0
            pace_min = int(pace_sec_per_mile // 60)
            pace_sec = int(pace_sec_per_mile % 60)
            print(f"Lap {lap['lapIndex']}: {round(dist_mi, 2)} mi in {round(lap['duration'],1)}s "
                f"→ pace {pace_min}:{pace_sec:02d}/mi | HR: {lap.get('averageHR')}")
    

    def get_activity_summary(self, client, activity_id) -> pd.DataFrame:
        """
        Fetch a single Garmin activity and return a one-row DataFrame with:
        - avg_hr, start_time, finish_time, pace (min/mile), distance (miles), elevation_gain, location
        """
        activity = client.get_activity(activity_id)
        summary = activity.get('summaryDTO', {}) if isinstance(activity, dict) else {}

        # Times
        start_str = summary.get('startTimeLocal') or summary.get('startTimeGMT')
        start_time = pd.to_datetime(start_str) if start_str else None
        duration_sec = summary.get('duration') or 0
        elapsed_sec = summary.get('elapsedDuration') or duration_sec
        finish_time = (start_time + pd.to_timedelta(elapsed_sec, unit='s')) if start_time is not None else None

        # Distance and pace
        distance_m = summary.get('distance') or 0.0
        distance_miles = distance_m / 1609.34 if distance_m else 0.0
        moving_sec = summary.get('movingDuration') or duration_sec
        # Decimal minutes per mile (e.g., 8.5)
        pace_min_per_mile = (moving_sec / distance_miles / 60) if distance_miles > 0 else None
        pace_float = round(pace_min_per_mile, 2) if pace_min_per_mile is not None else None

        # Other fields
        avg_hr = summary.get('averageHR') or 0
        elevation_gain = (summary.get('elevationGain') or 0.0) * 3.28084 # Convert to feet
        longitude = summary.get('startLongitude') or None
        latitude = summary.get('startLatitude') or None
        row = {
            'activity_id': activity.get('activityId') if isinstance(activity, dict) else activity_id,
            'activity_name': activity.get('activityName') if isinstance(activity, dict) else None,
            'start_time': start_time,
            'finish_time': finish_time,
            'distance_miles': round(distance_miles, 2),
            'pace': pace_float,
            'avg_hr': avg_hr,
            'elevation_gain': elevation_gain,
            'longitude': longitude,
            'latitude': latitude,
        }
        return pd.DataFrame([row])
    
    def get_activity_weather(self, activity_summary):


        activity_id = activity_summary.iloc[0]['activity_id']
        if activity_summary.iloc[0]['latitude'] is None or activity_summary.iloc[0]['longitude'] is None:
            raise Exception("Latitude or longitude is None")
        latitude = activity_summary.iloc[0]['latitude']
        longitude = activity_summary.iloc[0]['longitude']
        start = activity_summary.iloc[0]['start_time']
        end = activity_summary.iloc[0]['finish_time']
        data = self.report_reader.fetch_weather_data_openweathermap(latitude, longitude, start, end)
       
        item = data[0] if isinstance(data, list) else data
        if not isinstance(item, dict):
            raise Exception("Item is not a dictionary")

        main = item.get('main', {})
        temperatures = main['temp']
        humidities = main['humidity']

        weather = pd.DataFrame([{
            'activity_id': activity_id,
            'temperature': temperatures,
            'humidity': humidities
    }])

        return weather
    
    def get_sleep_data(self, activity_summary, client):
        activity_id = activity_summary.iloc[0]['activity_id']
        start_time = activity_summary.iloc[0]['start_time']
        
        # Garmin client expects a 'YYYY-MM-DD' string
        try:
            start_date_str = start_time.date().isoformat()
            print('Start date string: ', start_date_str)
        except Exception:
            # Fallback if already a string or not a Timestamp/date
            start_date_str = str(start_time)
        sleep_data = client.get_sleep_data(start_date_str)
        
        try:
            hrv_data = client.get_hrv_data(start_date_str)
            hrv = hrv_data['hrvSummary']['lastNightAvg']
            
        except Exception:
            hrv = None

        try:
            resting_heart_rate = sleep_data['restingHeartRate']
        except Exception:
            resting_heart_rate = None
        
        sleep = pd.DataFrame([{
            'activity_id': activity_id,
            'hrv': hrv,
            'resting_heart_rate': resting_heart_rate
        }])
        return sleep

    def list_activities(self, client, start_date, end_date) -> pd.DataFrame:
        """
        List running activities between start_date and end_date as per-activity summaries.

        Returns a DataFrame with: activity_id, name, date, type, distance_miles, avg_hr, pace_min_per_mile
        """
        if isinstance(start_date, str):
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        elif isinstance(start_date, datetime):
            start_dt = start_date
        elif isinstance(start_date, date):
            start_dt = datetime.combine(start_date, datetime.min.time())
        else:
            raise TypeError("start_date must be a datetime, date, or 'YYYY-MM-DD' string")

        if isinstance(end_date, str):
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        elif isinstance(end_date, datetime):
            end_dt = end_date
        elif isinstance(end_date, date):
            end_dt = datetime.combine(end_date, datetime.min.time())
        else:
            raise TypeError("end_date must be a datetime, date, or 'YYYY-MM-DD' string")

        api_start = start_dt.strftime('%Y-%m-%d')
        api_end = end_dt.strftime('%Y-%m-%d')

        activities = client.get_activities_by_date(api_start, api_end)

        rows = []
        for activity in activities:
            activity_type = activity.get('activityType', {}).get('typeKey', '').lower()
            if activity_type not in ['treadmill_running', 'running', 'manual', 'track_running']:
                continue
            distance_m = activity.get('distance') or 0.0
            distance_miles = distance_m / 1609.34 if distance_m else 0.0
            duration_sec = activity.get('duration') or 0
            pace_min_per_mile = (duration_sec / 60 / distance_miles) if distance_miles > 0 else None
            rows.append({
                'activity_id': activity.get('activityId'),
                'name': activity.get('activityName'),
                'date': activity.get('startTimeLocal'),
                'type': activity_type,
                'distance_miles': round(distance_miles, 2),
                'avg_hr': activity.get('averageHR'),
                'pace_min_per_mile': round(pace_min_per_mile, 2) if pace_min_per_mile is not None else None,
            })
        return pd.DataFrame(rows)

    def get_health_snapshot(self, client, target_date) -> pd.DataFrame:
        """
        Return sleep, HRV, and resting heart rate for a given date.

        Returns a one-row DataFrame with: date, sleep_score, hrv, resting_heart_rate
        """
        if isinstance(target_date, str):
            date_str = target_date
        elif isinstance(target_date, (datetime, date)):
            date_str = target_date.strftime('%Y-%m-%d')
        else:
            raise TypeError("target_date must be a datetime, date, or 'YYYY-MM-DD' string")

        sleep_data = client.get_sleep_data(date_str)
        try:
            hrv_data = client.get_hrv_data(date_str)
            hrv = hrv_data['hrvSummary']['lastNightAvg']
        except Exception:
            hrv = None

        resting_heart_rate = sleep_data.get('restingHeartRate') if isinstance(sleep_data, dict) else None
        sleep_score = None
        if isinstance(sleep_data, dict):
            sleep_score = (
                sleep_data.get('dailySleepDTO', {})
                .get('sleepScores', {})
                .get('overall', {})
                .get('value')
            )

        return pd.DataFrame([{
            'date': date_str,
            'sleep_score': sleep_score,
            'hrv': hrv,
            'resting_heart_rate': resting_heart_rate,
        }])

    def get_days_since_start(self, activity_summary):
        activity_id = activity_summary.iloc[0]['activity_id']
        activity_start_time = activity_summary.iloc[0]['start_time'].date()
        start_date = datetime(REGRESSION_START_DATE_YEAR, REGRESSION_START_DATE_MONTH, REGRESSION_START_DATE_DAY).date()
        days_since_start = (activity_start_time - start_date).days
        return pd.DataFrame([{
            'activity_id': activity_id,
            'days_since_start': days_since_start
        }])



# for index, activity in data_df.iterrows():
#     #Gets long.lat, start, and stop
#     lat = activity['start_lat']
#     long = activity['start_long']
#     start = activity['start_time']
#     stop = activity['stop_time']


#     start_full = pd.to_datetime(activity['start_time'], utc=True) #2024-06-03 07:45:12+00:00
#     start_hour = start_full.floor('h') #2024-06-03 07:00:00+00:00
#     start_day = start_full.date() # 2024-06-03

#     stop_full = pd.to_datetime(activity['stop_time'], utc=True) #2024-06-03 07:45:12+00:00
#     stop_hour = stop_full.floor('h') #2024-06-03 07:00:00+00:00
#     stop_day = start_full.date() #2024-06-03

#     time = activity['elapsed_time']
#     # Convert to total seconds
#     h, m, s = map(float, time.split(':'))
#     total_seconds = h * 3600 + m * 60 + s

#     # Convert to total minutes or hours
#     total_minutes = total_seconds / 60

#     #This calculates pace in minutes
#     data_df.at[index, 'Pace'] = total_minutes/activity['distance']

#     #This calculates the time variable that will be used in regression
#     data_df.at[index, 'Time'] = start_full - first_activity_time


#     #Get weather data
#     weather_data = fetch_weather_data(lat, long, start_day, stop_day)
#     weather_df = process_weather_data(weather_data)

#     for index2, row in weather_df.iterrows():
#         if start_hour == row['Time']:
#             data_df.at[index, 'Temp'] = row['Temperature (°F)']
#             data_df.at[index, 'Humid'] = row['Humidity (%)']