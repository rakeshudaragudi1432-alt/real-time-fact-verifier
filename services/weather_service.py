"""
Weather Service Module

Fetches live real-time weather data for specified geographic locations.
Supports Open-Meteo API (free, no key required) with optional fallback/primary
support for OpenWeatherMap if WEATHER_API_KEY is configured in .env.
"""

import os
import requests
from datetime import datetime
from typing import Dict, Any, Optional


import time
import logging

logger = logging.getLogger("WeatherService")


class WeatherService:
    """
    Handles geocoding and live weather data retrieval from external APIs.
    """

    def __init__(self, api_key: Optional[str] = None):
        # Read API Key from parameter or environment
        self.api_key = api_key or os.getenv("WEATHER_API_KEY", "").strip()
        # Avoid treating template placeholder string as real key
        if self.api_key == "your_weather_api_key_here":
            self.api_key = ""
        self._cache: Dict[str, tuple[float, Dict[str, Any]]] = {}

    def get_weather(self, location_name: str) -> Dict[str, Any]:
        """
        Retrieves real-time weather information for a location.
        First geocodes location, then queries current weather endpoints.
        """
        if not location_name or not location_name.strip():
            return {
                "status": "error",
                "error_message": "No location provided for weather lookup.",
                "location": None,
                "data": None
            }

        cleaned_location = location_name.strip()
        cache_key = cleaned_location.lower()
        now = time.time()

        # Return cached response if under 60 seconds TTL
        if cache_key in self._cache:
            cached_time, cached_res = self._cache[cache_key]
            if now - cached_time < 60:
                logger.info(f"Returning cached weather data for '{cleaned_location}'")
                return cached_res

        logger.info(f"Fetching live weather for location: '{cleaned_location}'")

        res = None
        # Attempt OpenWeatherMap if key is provided
        if self.api_key:
            owm_result = self._fetch_openweathermap(cleaned_location)
            if owm_result["status"] == "success":
                res = owm_result

        if not res:
            # Fallback to Open-Meteo (Free live weather API, zero key needed)
            res = self._fetch_openmeteo(cleaned_location)

        if res and res.get("status") == "success":
            self._cache[cache_key] = (now, res)

        return res

    def _fetch_openmeteo(self, location_name: str) -> Dict[str, Any]:
        """
        Fetches live weather from Open-Meteo Geocoding & Forecast API.
        """
        try:
            # Step 1: Geocoding
            geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
            geo_params = {
                "name": location_name,
                "count": 1,
                "language": "en",
                "format": "json"
            }
            geo_resp = requests.get(geocode_url, params=geo_params, timeout=8)
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()

            if not geo_data.get("results"):
                return {
                    "status": "error",
                    "error_message": f"Location '{location_name}' could not be found.",
                    "location": location_name,
                    "data": None
                }

            loc_result = geo_data["results"][0]
            lat = loc_result["latitude"]
            lon = loc_result["longitude"]
            resolved_city = loc_result.get("name", location_name)
            country = loc_result.get("country", "")

            # Step 2: Forecast & Current Weather
            weather_url = "https://api.open-meteo.com/v1/forecast"
            weather_params = {
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,rain,weather_code,cloud_cover,wind_speed_10m"
            }
            w_resp = requests.get(weather_url, params=weather_params, timeout=8)
            w_resp.raise_for_status()
            w_data = w_resp.json()

            current = w_data.get("current", {})
            temp_c = current.get("temperature_2m")
            humidity = current.get("relative_humidity_2m")
            precip = current.get("precipitation", 0.0)
            rain = current.get("rain", 0.0)
            cloud_cover = current.get("cloud_cover", 0)
            wind_speed = current.get("wind_speed_10m", 0.0)
            weather_code = current.get("weather_code", 0)

            condition_desc, is_raining = self._interpret_wmo_code(weather_code, precip, rain)
            temp_f = round((temp_c * 9/5) + 32, 1) if temp_c is not None else None

            now_str = datetime.now().strftime("%d %B %Y, %I:%M %p")

            return {
                "status": "success",
                "error_message": None,
                "location": resolved_city,
                "country": country,
                "latitude": lat,
                "longitude": lon,
                "temperature_c": round(temp_c, 1) if temp_c is not None else None,
                "temperature_f": temp_f,
                "humidity": humidity,
                "condition": condition_desc,
                "is_raining": is_raining,
                "precipitation_mm": precip,
                "cloud_cover_percent": cloud_cover,
                "wind_speed_kmh": wind_speed,
                "source": "Open-Meteo Real-Time Weather API",
                "verification_time": now_str
            }

        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "error_message": "Weather API connection timed out. Please try again.",
                "location": location_name,
                "data": None
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "error_message": f"Unable to retrieve live weather data ({str(e)}).",
                "location": location_name,
                "data": None
            }
        except Exception as e:
            return {
                "status": "error",
                "error_message": f"An unexpected error occurred during weather retrieval: {str(e)}",
                "location": location_name,
                "data": None
            }

    def _fetch_openweathermap(self, location_name: str) -> Dict[str, Any]:
        """
        Fetches weather using OpenWeatherMap API key if available.
        """
        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": location_name,
                "appid": self.api_key,
                "units": "metric"
            }
            resp = requests.get(url, params=params, timeout=8)
            if resp.status_code != 200:
                return {"status": "error", "error_message": "OpenWeatherMap query failed."}

            data = resp.json()
            main = data.get("main", {})
            weather_list = data.get("weather", [{}])
            wind = data.get("wind", {})

            temp_c = main.get("temp")
            temp_f = round((temp_c * 9/5) + 32, 1) if temp_c is not None else None
            condition = weather_list[0].get("main", "Clear")
            desc = weather_list[0].get("description", condition).capitalize()

            is_raining = "rain" in condition.lower() or "drizzle" in condition.lower() or "thunderstorm" in condition.lower()
            now_str = datetime.now().strftime("%d %B %Y, %I:%M %p")

            return {
                "status": "success",
                "error_message": None,
                "location": data.get("name", location_name),
                "country": data.get("sys", {}).get("country", ""),
                "latitude": data.get("coord", {}).get("lat"),
                "longitude": data.get("coord", {}).get("lon"),
                "temperature_c": round(temp_c, 1) if temp_c is not None else None,
                "temperature_f": temp_f,
                "humidity": main.get("humidity"),
                "condition": desc,
                "is_raining": is_raining,
                "precipitation_mm": 0.0,
                "cloud_cover_percent": data.get("clouds", {}).get("all", 0),
                "wind_speed_kmh": round(wind.get("speed", 0) * 3.6, 1),
                "source": "OpenWeatherMap REST API",
                "verification_time": now_str
            }
        except Exception:
            return {"status": "error", "error_message": "OpenWeatherMap error."}

    def _interpret_wmo_code(self, code: int, precip: float, rain: float) -> tuple[str, bool]:
        """
        Translates WMO weather code into readable condition string and rain boolean.
        """
        is_raining = precip > 0.1 or rain > 0.1 or code in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99]

        code_map = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            95: "Thunderstorm",
            96: "Thunderstorm with light hail",
            99: "Thunderstorm with heavy hail"
        }

        condition = code_map.get(code, "Clear")
        return condition, is_raining
