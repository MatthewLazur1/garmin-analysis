from garminconnect import (
    Garmin,
    GarminConnectConnectionError,
    GarminConnectAuthenticationError,
    GarminConnectTooManyRequestsError,
)
import garminconnect
import datetime
import requests
import pandas as pd
from dotenv import load_dotenv
import os
import garth

class ReportReader:
    def __init__(self):
        self.report = {}

    def fetch_weather_data(latitude, longitude, start_date, end_date):
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": "temperature_2m,relative_humidity_2m",
            "temperature_unit": "fahrenheit",
            "timezone": "America/New_York"  # Adjust the timezone as needed
        }

        response = requests.get(url, params=params)

        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            raise Exception(f"Error fetching data: {response.status_code} - {response.text}")
    
    def fetch_garmin_data(self):
        """
            Fetch Garmin client with persistent auth via Garth.
        """
        load_dotenv()
        email = os.getenv("GARMIN_EMAIL")
        password = os.getenv("GARMIN_PASSWORD")

        try:
            # Try loading saved session first
            garth.client.load_session()
            garmin = garminconnect.Garmin()
            garmin.login()  # Validate session
            print(f"Logged in as: {garmin.display_name}")
            return garmin

        except Exception as e:
            print(f"No saved session found. Attempting fresh login... Error: {e}")

        try:
            # Fresh login
            garmin = garminconnect.Garmin(email, password)
            garmin.login()
            print(f"Logged in as: {garmin.display_name}")

            # Save session for future use
            garth.client.dump_session()
            return garmin

        except (
            GarminConnectConnectionError,
            GarminConnectAuthenticationError,
            GarminConnectTooManyRequestsError,
        ) as err:
            print(f"Error: {err}")
            raise
    