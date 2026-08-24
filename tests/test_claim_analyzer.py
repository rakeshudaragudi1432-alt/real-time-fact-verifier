"""
Unit Tests for Claim Analyzer Service Module
Verifies classification and entity extraction across all 6 supported categories:
weather, sports, movies, science, news, unknown.
"""

import unittest
from services.claim_analyzer import ClaimAnalyzer, analyze_claim


class TestClaimAnalyzer(unittest.TestCase):

    def test_weather_claim_analysis(self):
        claim = "Today the temperature in Vijayawada is 28 degrees."
        result = analyze_claim(claim)

        self.assertEqual(result["category"], "weather")
        self.assertEqual(result["location"], "Vijayawada")
        self.assertEqual(result["subject"], "temperature")
        self.assertEqual(result["date"], "today")
        self.assertIn("temperature", result["keywords"])
        self.assertIn("vijayawada", [k.lower() for k in result["keywords"]])
        self.assertEqual(result["claim_text"], claim)

    def test_sports_claim_analysis(self):
        claim = "India won today's cricket match."
        result = analyze_claim(claim)

        self.assertEqual(result["category"], "sports")
        self.assertEqual(result["subject"], "cricket match")
        self.assertEqual(result["date"], "today")
        self.assertIn("cricket", result["keywords"])
        self.assertIn("won", result["keywords"])

    def test_movie_claim_analysis(self):
        claim = "The movie Avatar 3 was released in 2025."
        result = analyze_claim(claim)

        self.assertEqual(result["category"], "movies")
        self.assertEqual(result["subject"], "release date")
        self.assertEqual(result["date"], "2025")
        self.assertIn("avatar", result["keywords"])
        self.assertIn("released", result["keywords"])

    def test_science_claim_analysis(self):
        claim = "NASA discovered a new planet."
        result = analyze_claim(claim)

        self.assertEqual(result["category"], "science")
        self.assertEqual(result["subject"], "astronomy discovery")
        self.assertIn("nasa", result["keywords"])
        self.assertIn("planet", result["keywords"])

    def test_science_speed_of_light_claim(self):
        claim = "The speed of light is approximately 300,000 km/s"
        result = analyze_claim(claim)

        self.assertEqual(result["category"], "science")
        self.assertEqual(result["subject"], "speed of light")

    def test_news_claim_analysis(self):
        claim = "The Prime Minister announced a new policy."
        result = analyze_claim(claim)

        self.assertEqual(result["category"], "news")
        self.assertEqual(result["subject"], "government policy")
        self.assertIn("minister", result["keywords"])
        self.assertIn("policy", result["keywords"])

    def test_unknown_claim_analysis(self):
        claim = "Xyz blorp random gibberish phrase 12345"
        result = analyze_claim(claim)

        self.assertEqual(result["category"], "unknown")
        self.assertIsNone(result["location"])
        self.assertIsNone(result["subject"])
        self.assertEqual(result["claim_text"], claim)

    def test_empty_and_invalid_inputs(self):
        self.assertEqual(analyze_claim("")["category"], "unknown")
        self.assertEqual(analyze_claim("   ")["category"], "unknown")
        self.assertEqual(analyze_claim(None)["category"], "unknown")
        self.assertEqual(analyze_claim(12345)["category"], "unknown")

    def test_case_insensitivity_and_whitespace(self):
        claim = "   TODAY THE TEMPERATURE IN HYDERABAD IS 32 DEGREES.   "
        result = analyze_claim(claim)

        self.assertEqual(result["category"], "weather")
        self.assertEqual(result["location"], "Hyderabad")
        self.assertEqual(result["date"], "today")
        self.assertEqual(result["claim_text"], "TODAY THE TEMPERATURE IN HYDERABAD IS 32 DEGREES.")


if __name__ == "__main__":
    unittest.main()
