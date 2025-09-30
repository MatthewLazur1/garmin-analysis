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
from garth.exc import GarthHTTPError

class ReportReader:
    def __init__(self):
        self.report = {}


    def fetch_weather_data_openweathermap(self, latitude, longitude, start_date, end_date):
        """
        Fetch weather data using OpenWeatherMap API (requires API key)
        """
        load_dotenv()
        api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        
        if not api_key:
            raise Exception("OPENWEATHERMAP_API_KEY not found in environment variables")
        
        # Convert dates to Unix timestamps
        start_timestamp = int(start_date.timestamp())
        end_timestamp = int(end_date.timestamp())
        url = "https://api.openweathermap.org/data/2.5/weather"
        
        weather_data = []
        current_timestamp = start_timestamp
        
        # OpenWeatherMap has a limit of 1000 calls per day for free tier
        # We'll fetch daily data to stay within limits
        while current_timestamp <= end_timestamp:
            params = {
                "lat": latitude,
                "lon": longitude,
                "dt": current_timestamp,
                "appid": api_key,
                "units": "imperial"  # Fahrenheit, mph, etc.
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                weather_data.append(data)
            elif response.status_code == 401:
                raise Exception("Invalid OpenWeatherMap API key")
            elif response.status_code == 429:
                raise Exception("OpenWeatherMap API rate limit exceeded")
            else:
                print(f"Warning: Failed to fetch weather data for {datetime.datetime.fromtimestamp(current_timestamp).strftime('%Y-%m-%d')}: {response.status_code}")
            
            # Move to next day
            current_timestamp += 86400  # 24 hours in seconds
        
        return weather_data

    def fetch_garmin_data(self):
        """
        Fetch Garmin client with persistent auth using garth token management.
        Based on example.py implementation.
        """
        load_dotenv()
        email = os.getenv("GARMIN_EMAIL")
        password = os.getenv("GARMIN_PASSWORD")
        tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"

        try:
            # Try loading saved session first (using garth approach from example.py)
            print(f"Trying to login to Garmin Connect using token data from directory '{tokenstore}'...")
            garmin = garminconnect.Garmin()
            garmin.login(tokenstore)
            print(f"Logged in as: {garmin.display_name}")
            return garmin

        except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError):
            # Session is expired or doesn't exist. Need to log in again
            print(f"Login tokens not present, login with your Garmin Connect credentials to generate them.\n"
                  f"They will be stored in '{tokenstore}' for future use.\n")
            
            try:
                # Fresh login with credentials (following example.py pattern)
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

                # Save Oauth1 and Oauth2 token files to directory for next login
                garmin.garth.dump(tokenstore)
                print(f"Oauth tokens stored in '{tokenstore}' directory for future use.\n")
                
                # Re-login Garmin API with tokens (following example.py pattern)
                garmin.login(tokenstore)
                print(f"Logged in as: {garmin.display_name}")
                return garmin

            except (
                FileNotFoundError,
                GarthHTTPError,
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
