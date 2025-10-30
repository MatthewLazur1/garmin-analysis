from report_objects.report_reader import ReportReader
from report_objects.report_manager import ReportManager
from report_objects.report_builder import ReportBuilder
from getpass import getpass
import garminconnect
from datetime import date, datetime, timedelta
import garth
import os
from dotenv import load_dotenv
import json
from predictive_models.regression_predictive_model import PredictivePacingModel

def main():
    report_reader = ReportReader()
    report_manager = ReportManager()
    builder = ReportBuilder()
    client = report_reader.fetch_garmin_data()
    
    start = datetime(2025, 8, 11)
    end = datetime(2025, 10, 15)
    api_start = start.strftime('%Y-%m-%d')   
    api_end = end.strftime('%Y-%m-%d')

    activity_summary = builder.get_activity_summary(client, 20692449472)
    regression_data = report_manager.get_regression_data(client)
    # regression_data.to_csv('regression_data.csv', index=False)
    # activities = client.get_activities_by_date(date(2025, 2, 1).strftime('%Y-%m-%d'), date(2025, 2, 10).strftime('%Y-%m-%d'))
    # for activity in activities:
    #     activity_summary = builder.get_activity_summary(client, activity['activityId'])
    #     sleep_data = builder.get_sleep_data(activity_summary, client)
    #     print('Sleep data: ', sleep_data)
    # sleep_data = client.get_sleep_data(start.date().isoformat())
    # hrv = sleep_data['avgOvernightHrv']
    # print('Sleep data: ', sleep_data)
    # print('HRV: ', hrv)

    predictive_pacing_model = PredictivePacingModel()
    predictive_pacing_model.train_model(regression_data)


    today_days_since_start = 656

    current_run_inputs = {
        'distance_miles': 10.0,      # User Goal (Target Miles)
        'avg_hr': 140,               # User Goal (Target HR Zone)
        'temperature': 67.0,         # Forecasted Temp
        'humidity': 66,              # Forecasted Humidity
        'hrv': 73,                   # Measured HRV (Today)
        'resting_heart_rate': 48,    # Measured RHR (Today)
        'days_since_start': today_days_since_start, 
        'elevation_gain': 375,
    }
    predicted_pace = predictive_pacing_model.predict_pace(current_run_inputs)

    vif, accuracy, coef_df, r_squared_train, r_squared_test = predictive_pacing_model.analyze_model()
    print("Model Analysis:")
    print("----------------------------------------------------------")
    print("VIF:")
    print(vif.to_string(index=False))
    print("VIF Threshold Guide: < 5 is good; 5-10 is concerning; > 10 is problematic.")
    print("----------------------------------------------------------")

    print("Model R-squared:")
    print(f"\nModel R-squared (Training): {r_squared_train:.3f}")
    print(f"Model R-squared (Test Set): {r_squared_test:.3f}")
    print("----------------------------------------------------------")

    print("Coefficients:")
    print(coef_df.to_string(index=False))
    print("----------------------------------------------------------")

    print("Accuracy:")
    print(accuracy)
    print("----------------------------------------------------------")
    
    print("\n========================================================")
    print("             PACE PREDICTION FOR TODAY                  ")
    print("========================================================")
    print(f"Goal Distance: {current_run_inputs['distance_miles']:.1f} miles")
    print(f"Goal Effort (Avg HR): {current_run_inputs['avg_hr']} BPM")
    print(f"Current Recovery (HRV/RHR): {current_run_inputs['hrv']}/{current_run_inputs['resting_heart_rate']}")
    print(f"\nPREDICTED PACE: {predicted_pace:.2f} min/mile")
    print("========================================================")
if __name__ == "__main__":
    main()