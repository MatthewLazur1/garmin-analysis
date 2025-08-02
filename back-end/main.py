from report_objects.report_reader import ReportReader
from report_objects.report_builder import ReportBuilder
from getpass import getpass
import garminconnect
from datetime import date, datetime, timedelta
import garth
import os
from dotenv import load_dotenv

def main():
    report_reader = ReportReader()
    report_builder = ReportBuilder()
    client = report_reader.fetch_garmin_data()
    # report_builder.show_activity_splits(19736220449, client)
    weekly_mileage = report_builder.aggregate_weekly_mileage(client, datetime(2025, 7, 14), datetime(2025, 7, 28), 7)
    print(weekly_mileage)
    
if __name__ == "__main__":
    main()