import datetime as dt
import meteomatics.api as api
import pandas as pd
import numpy as np
import os

class WeatherService:
    """Get weather related information."""
    def __init__(self):
        METEOMATICS_USERNAME = os.getenv("METEOMATICS_USERNAME")
        print(METEOMATICS_USERNAME)
        METEOMATICS_PASSWORD = os.getenv("METEOMATICS_PASSWORD")
        print(METEOMATICS_PASSWORD)
        self.username = METEOMATICS_USERNAME
        self.password = METEOMATICS_PASSWORD

    def get_weather(self, latitude, longitude):
        """Fetch weather data for given latitude and longitude from Meteomatics API."""
        print("Getting Weather Forecast")
        if not latitude or not longitude:
            return "Invalid location. Cannot fetch weather data."

        coordinates = [(latitude, longitude)]
        parameters = [
            "t_2m:C", "t_max_2m_24h:C", "t_min_2m_24h:C",
            "wind_speed_10m:ms", "wind_dir_10m:d", "precip_1h:mm",
            "uv:idx", "weather_symbol_1h:idx", "sunrise:sql", "sunset:sql"
        ]

        startdate = dt.datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        df = api.query_time_series(coordinates, startdate, startdate, dt.timedelta(hours=1), parameters, self.username, self.password, model="mix")

        params = {
            "t_2m:C": "Temperature (°C)", "t_max_2m_24h:C": "Max Temperature (°C)",
            "t_min_2m_24h:C": "Min Temperature (°C)", "wind_speed_10m:ms": "Wind Speed (m/s)",
            "wind_dir_10m:d": "Wind Direction (°)", "precip_1h:mm": "Precipitation (mm)",
            "uv:idx": "UV Index", "weather_symbol_1h:idx": "Weather Condition",
            "sunrise:sql": "Sunrise Time", "sunset:sql": "Sunset Time"
        }

        weather_data = {}
        for param, name in params.items():
            value = df[param].values[0]
            if isinstance(value, (pd.Timestamp, np.datetime64)):
                value = pd.to_datetime(value, utc=True).tz_convert("Asia/Kolkata").strftime("%Y-%m-%d %H:%M:%S %Z")
            weather_data[name] = value

        return weather_data