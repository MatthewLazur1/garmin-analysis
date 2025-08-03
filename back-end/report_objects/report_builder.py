import pandas as pd
from datetime import datetime, timedelta
import json

class ReportBuilder:
    def __init__(self):
        self.report = {}
    
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
        # Convert dates to datetime if they're not already
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Get activities for the date range
        activities = client.get_activities_by_date(start_date, end_date)
        # with open('activities.json', 'w') as f:
        #     json.dump(activities, f, indent=4)
        # Filter for running activities
        running_activities = []
        for activity in activities:
            activity_type = activity.get('activityType', {}).get('typeKey', '').lower()
            if activity_type in ['treadmill_running', 'running', 'manual']:
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
            'mean'   # Average distance per activity
        ]).round(2)
        
        # Rename columns for clarity
        weekly_mileage.columns = ['Total_Miles', 'Activity_Count', 'Avg_Distance_Miles']
        
        # Convert period index to show week range more clearly
        # weekly_mileage.index = [f"{period.start_time.strftime('%Y-%m-%d')} to {period.end_time.strftime('%Y-%m-%d')}" 
        #                        for period in weekly_mileage.index]
        
        # Alternative: Show just the week start date for cleaner display
        weekly_mileage.index = [f"Week of {period.start_time.strftime('%Y-%m-%d')}" 
                               for period in weekly_mileage.index]
        
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
    
    
    def process_weather_data(data):
        hourly = data['hourly']
        hourly_times = pd.to_datetime(hourly['time'], utc=True)
        temperatures = hourly['temperature_2m']
        humidities = hourly['relative_humidity_2m']

        weather = pd.DataFrame({
            'Time': hourly_times,
            'Temperature (°F)': temperatures,
            'Humidity (%)': humidities
    })

        return weather


# #Get dataframe of garmin data
# data_df = get_data(results)

# #Add empty column to be added to in next for loop
# data_df['Temp'] = None
# data_df['Humid'] = None
# data_df['Pace'] = None
# data_df['Time'] = None

# data_df = data_df.sort_values(by='start_time', ascending=True)

# first_activity_time = pd.to_datetime(data_df['start_time'].iloc[0], utc=True)

# #Adds the Temp and Humid to Dataframe
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