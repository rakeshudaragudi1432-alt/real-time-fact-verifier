"""
Unit Tests for Weather Service Module
Tests live weather fetching, geocoding, error handling, and invalid locations.
"""

import unittest
from unittest.mock import patch, MagicMock
from services.weather_service import WeatherService


class TestWeatherService(unittest.TestCase):

    def setUp(self):
        self.service = WeatherService()

    def test_weather_service_instantiation(self):
        self.assertIsNotNone(self.service)

    def test_empty_location_returns_error(self):
        res = self.service.get_weather("")
        self.assertEqual(res["status"], "error")
        self.assertIn("No location provided", res["error_message"])

    def test_invalid_location_returns_error(self):
        res = self.service.get_weather("XyzNonExistentCity9999")
        self.assertEqual(res["status"], "error")
        self.assertIn("could not be found", res["error_message"])

    @patch("services.weather_service.requests.get")
    def test_mocked_successful_openmeteo_fetch(self, mock_get):
        # Mock geocoding response
        geo_response = MagicMock()
        geo_response.status_code = 200
        geo_response.json.return_value = {
            "results": [
                {
                    "name": "Vijayawada",
                    "latitude": 16.5062,
                    "longitude": 80.6480,
                    "country": "India"
                }
            ]
        }

        # Mock weather response
        weather_response = MagicMock()
        weather_response.status_code = 200
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": 28.5,
                "relative_humidity_2m": 65,
                "precipitation": 0.0,
                "rain": 0.0,
                "weather_code": 1,
                "cloud_cover": 20,
                "wind_speed_10m": 12.0
            }
        }

        mock_get.side_effect = [geo_response, weather_response]

        res = self.service.get_weather("Vijayawada")

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["location"], "Vijayawada")
        self.assertEqual(res["temperature_c"], 28.5)
        self.assertFalse(res["is_raining"])
        self.assertEqual(res["source"], "Open-Meteo Real-Time Weather API")


if __name__ == "__main__":
    unittest.main()
