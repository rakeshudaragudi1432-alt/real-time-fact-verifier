"""
Unit Tests for Fact Verifier Module (Weather, Sports, Movies & Science Integration)
Tests updated for Stage 8 result format: 'VERIFIED ✅', 'NOT VERIFIED ❌', 'UNCERTAIN ⚠️'
"""

import unittest
from unittest.mock import patch
from verification.verifier import FactVerifier


class TestFactVerifier(unittest.TestCase):

    def setUp(self):
        self.verifier = FactVerifier()

    def test_empty_claim_returns_uncertain(self):
        res = self.verifier.verify("")
        self.assertIn("UNCERTAIN", res["result"])
        self.assertEqual(res["detected_domain"], "unknown")

    def test_weather_claim_without_location_returns_uncertain(self):
        """A weather claim with no extractable location should return UNCERTAIN."""
        res = self.verifier.verify("The temperature is 28 degrees")
        self.assertIn("UNCERTAIN", res["result"])
        self.assertEqual(res["detected_domain"], "WEATHER")

    def test_very_short_input_returns_uncertain(self):
        res = self.verifier.verify("hello")
        self.assertIn("UNCERTAIN", res["result"])

    def test_random_text_returns_uncertain(self):
        res = self.verifier.verify("xyz abc 123 blorp")
        self.assertIn("UNCERTAIN", res["result"])

    def test_long_input_is_truncated_safely(self):
        long_claim = "The temperature in Vijayawada is 28 degrees Celsius. " * 50
        res = self.verifier.verify(long_claim)
        # Must not crash; result must be a string
        self.assertIsInstance(res["result"], str)

    @patch("services.weather_service.WeatherService.get_weather")
    def test_full_weather_verification_matching_temp(self, mock_get_weather):
        mock_get_weather.return_value = {
            "status": "success",
            "location": "Vijayawada",
            "country": "India",
            "temperature_c": 28.0,
            "temperature_f": 82.4,
            "humidity": 60,
            "condition": "Mainly clear",
            "is_raining": False,
            "cloud_cover_percent": 20,
            "wind_speed_kmh": 10.0,
            "precipitation_mm": 0.0,
            "source": "Open-Meteo Real-Time Weather API",
            "verification_time": "24 August 2026, 6:30 PM"
        }

        res = self.verifier.verify("Vijayawada temperature is 28°C")

        self.assertIn("VERIFIED", res["result"])
        self.assertEqual(res["detected_location"], "Vijayawada")
        self.assertEqual(res["detected_domain"], "WEATHER")

    @patch("services.weather_service.WeatherService.get_weather")
    def test_weather_verification_wrong_temp(self, mock_get_weather):
        mock_get_weather.return_value = {
            "status": "success",
            "location": "Mumbai",
            "country": "India",
            "temperature_c": 32.0,
            "temperature_f": 89.6,
            "humidity": 75,
            "condition": "Partly cloudy",
            "is_raining": False,
            "cloud_cover_percent": 50,
            "wind_speed_kmh": 15.0,
            "precipitation_mm": 0.0,
            "source": "Open-Meteo Real-Time Weather API",
            "verification_time": "24 August 2026, 6:30 PM"
        }

        # Claiming 100°C in Mumbai should return NOT VERIFIED
        res = self.verifier.verify("Temperature in Mumbai is 100°C")
        self.assertIn("NOT VERIFIED", res["result"])
        self.assertEqual(res["detected_domain"], "WEATHER")

    @patch("services.weather_service.WeatherService.get_weather")
    def test_weather_api_failure_returns_uncertain(self, mock_get_weather):
        mock_get_weather.return_value = {
            "status": "error",
            "error_message": "Unable to geocode location."
        }

        res = self.verifier.verify("The weather in XYZ123CityFake is sunny.")
        self.assertIn("UNCERTAIN", res["result"])
        self.assertEqual(res["detected_domain"], "WEATHER")

    @patch("services.science_service.ScienceService.fetch_science_data")
    def test_science_verification_moon_satellite(self, mock_fetch_science):
        mock_fetch_science.return_value = {
            "status": "success",
            "topic": "Moon",
            "title": "Moon",
            "extract": "The Moon is the only natural satellite of Earth.",
            "source_name": "Wikimedia Scientific Knowledge Base REST API",
            "source_url": "https://en.wikipedia.org/wiki/Moon"
        }

        res = self.verifier.verify("The Moon is Earth's natural satellite.")

        self.assertIn("VERIFIED", res["result"])
        self.assertEqual(res["detected_domain"], "SCIENCE")
        self.assertIn("natural satellite of Earth", res["explanation"])

    @patch("services.science_service.ScienceService.fetch_science_data")
    def test_science_verification_largest_planet_false(self, mock_fetch_science):
        mock_fetch_science.return_value = {
            "status": "success",
            "topic": "Earth",
            "title": "Earth",
            "extract": "Earth is the fifth-largest planet in the Solar System.",
            "source_name": "Wikimedia Scientific Knowledge Base REST API",
            "source_url": "https://en.wikipedia.org/wiki/Earth"
        }

        res = self.verifier.verify("The Earth is the largest planet in the Solar System.")

        self.assertIn("NOT VERIFIED", res["result"])
        self.assertEqual(res["detected_domain"], "SCIENCE")
        self.assertIn("Jupiter is the largest planet", res["explanation"])

    @patch("services.science_service.ScienceService.fetch_science_data")
    def test_science_earth_fourth_planet_false(self, mock_fetch_science):
        mock_fetch_science.return_value = {
            "status": "success",
            "topic": "Earth",
            "title": "Earth",
            "extract": "Earth is the third planet from the Sun and the fifth largest.",
            "source_name": "Wikimedia Scientific Knowledge Base REST API",
            "source_url": "https://en.wikipedia.org/wiki/Earth"
        }

        res = self.verifier.verify("Earth is the fourth planet from the Sun.")
        self.assertIn("NOT VERIFIED", res["result"])
        self.assertIn("3rd planet", res["explanation"])

    @patch("services.science_service.ScienceService.fetch_science_data")
    def test_science_verification_uncertain(self, mock_fetch_science):
        mock_fetch_science.return_value = {
            "status": "error",
            "error_message": "No scientific data found."
        }

        res = self.verifier.verify("Quantum teleportation created a time machine in 2030")

        self.assertIn("UNCERTAIN", res["result"])
        self.assertEqual(res["detected_domain"], "SCIENCE")

    @patch("services.movie_service.MovieService.fetch_movie_info")
    def test_movie_correct_year_verified(self, mock_movie):
        mock_movie.return_value = {
            "status": "success",
            "title": "Interstellar",
            "year": "2014",
            "release_date": "07 Nov 2014",
            "director": "Christopher Nolan",
            "actors": ["Matthew McConaughey", "Anne Hathaway"],
            "actors_raw": "Matthew McConaughey, Anne Hathaway, Jessica Chastain",
            "rating": 8.7,
            "rating_raw": "8.7",
            "genre_raw": "Adventure, Drama, Sci-Fi",
            "runtime": "169 min",
            "source": "OMDb / IMDb Movie Database API"
        }

        res = self.verifier.verify("Interstellar was released in 2014.")
        self.assertIn("VERIFIED", res["result"])
        self.assertEqual(res["detected_domain"], "MOVIES")

    @patch("services.movie_service.MovieService.fetch_movie_info")
    def test_movie_wrong_year_not_verified(self, mock_movie):
        mock_movie.return_value = {
            "status": "success",
            "title": "Interstellar",
            "year": "2014",
            "release_date": "07 Nov 2014",
            "director": "Christopher Nolan",
            "actors": ["Matthew McConaughey"],
            "actors_raw": "Matthew McConaughey, Anne Hathaway",
            "rating": 8.7,
            "rating_raw": "8.7",
            "genre_raw": "Sci-Fi",
            "runtime": "169 min",
            "source": "OMDb / IMDb Movie Database API"
        }

        res = self.verifier.verify("Interstellar was released in 2018.")
        self.assertIn("NOT VERIFIED", res["result"])
        self.assertEqual(res["detected_domain"], "MOVIES")

    @patch("services.movie_service.MovieService.fetch_movie_info")
    def test_movie_director_verified(self, mock_movie):
        mock_movie.return_value = {
            "status": "success",
            "title": "The Dark Knight",
            "year": "2008",
            "release_date": "18 Jul 2008",
            "director": "Christopher Nolan",
            "actors": ["Christian Bale", "Heath Ledger"],
            "actors_raw": "Christian Bale, Heath Ledger, Aaron Eckhart",
            "rating": 9.0,
            "rating_raw": "9.0",
            "genre_raw": "Action, Crime, Drama",
            "runtime": "152 min",
            "source": "OMDb / IMDb Movie Database API"
        }

        res = self.verifier.verify("The Dark Knight was directed by Christopher Nolan.")
        self.assertIn("VERIFIED", res["result"])
        self.assertEqual(res["detected_domain"], "MOVIES")
        self.assertIn("Christopher Nolan", res["explanation"])

    @patch("services.sports_service.SportsService.fetch_sports_data")
    def test_sports_loss_claim_verified(self, mock_sports):
        mock_sports.return_value = {
            "status": "success",
            "extracted_teams": ["Barcelona"],
            "matched_event": {
                "event_title": "Real Madrid vs Barcelona",
                "league": "La Liga",
                "date": "2026-05-10",
                "home_team": "Real Madrid",
                "away_team": "Barcelona",
                "home_score": 3,
                "away_score": 1,
                "winner": "Real Madrid"
            },
            "source": "TheSportsDB Real-Time Sports API"
        }

        res = self.verifier.verify("Barcelona lost their last game.")
        self.assertIn("VERIFIED", res["result"])
        self.assertEqual(res["detected_domain"], "SPORTS")

    @patch("services.science_service.ScienceService.fetch_science_data")
    def test_science_water_freeze_verified(self, mock_science):
        mock_science.return_value = {
            "status": "success",
            "topic": "Water",
            "title": "Water",
            "extract": "Water freezes at 0 °C (32 °F; 273 K) under standard atmospheric pressure.",
            "source_name": "Wikimedia Scientific Knowledge Base REST API",
            "source_url": "https://en.wikipedia.org/wiki/Water"
        }

        res = self.verifier.verify("Water freezes at 0 degrees Celsius under standard atmospheric pressure.")
        self.assertIn("VERIFIED", res["result"])
        self.assertEqual(res["detected_domain"], "SCIENCE")

    def test_unknown_domain_returns_clear_message(self):
        res = self.verifier.verify("xyz abc 123")
        self.assertIn("UNCERTAIN", res["result"])
        self.assertIn("Unable to determine the verification domain", res["explanation"])


if __name__ == "__main__":
    unittest.main()
