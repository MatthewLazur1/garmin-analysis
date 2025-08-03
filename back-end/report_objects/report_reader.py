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
        Fetch Garmin client with persistent auth using token-based authentication.
        """
        load_dotenv()
        email = os.getenv("GARMIN_EMAIL")
        password = os.getenv("GARMIN_PASSWORD")
        tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"

        try:
            # Try loading saved session first
            print(f"Trying to login to Garmin Connect using token data from directory '{tokenstore}'...")
            garmin = garminconnect.Garmin()
            garmin.login(tokenstore)
            print(f"Logged in as: {garmin.display_name}")
            return garmin

        except (FileNotFoundError, garth.exc.GarthHTTPError, GarminConnectAuthenticationError):
            # Session is expired or doesn't exist. Need to log in again
            print(f"Login tokens not present, login with your Garmin Connect credentials to generate them.\n"
                  f"They will be stored in '{tokenstore}' for future use.\n")
            
            try:
                # Fresh login with credentials
                garmin = garminconnect.Garmin(
                    email=email, 
                    password=password, 
                    is_cn=False, 
                    return_on_mfa=True
                )
                result1, result2 = garmin.login()
                
                # Handle MFA if required
                if result1 == "needs_mfa":
                    mfa_code = input("MFA one-time code: ")
                    garmin.resume_login(result2, mfa_code)

                # Save tokens for future use
                garmin.garth.dump(tokenstore)
                print(f"Oauth tokens stored in '{tokenstore}' directory for future use.\n")
                
                # Re-login with tokens for consistency
                garmin.login(tokenstore)
                print(f"Logged in as: {garmin.display_name}")
                return garmin

            except (
                FileNotFoundError,
                garth.exc.GarthHTTPError,
                GarminConnectAuthenticationError,
                requests.exceptions.HTTPError,
            ) as err:
                print(f"Error during login: {err}")
                raise

        except (
            GarminConnectConnectionError,
            GarminConnectTooManyRequestsError,
        ) as err:
            print(f"Error: {err}")
            raise
        