"""
Unit Tests for Sports Service Module
"""

import unittest
from unittest.mock import patch, MagicMock
from services.sports_service import SportsService


class TestSportsService(unittest.TestCase):

    def setUp(self):
        self.service = SportsService()

    def test_sports_service_instantiation(self):
        self.assertIsNotNone(self.service)

    def test_empty_claim_returns_error(self):
        res = self.service.fetch_sports_data("", {})
        self.assertEqual(res["status"], "error")
        self.assertIn("Invalid claim input", res["error_message"])

    def test_no_team_or_player_returns_error(self):
        res = self.service.fetch_sports_data("Some random sentence without sports team or player", {})
        self.assertEqual(res["status"], "error")
        self.assertIn("Could not identify a specific team", res["error_message"])

    @patch("services.sports_service.requests.get")
    def test_mocked_successful_sports_query(self, mock_get):
        # Mock searchteams response
        t_resp = MagicMock()
        t_resp.status_code = 200
        t_resp.json.return_value = {
            "teams": [
                {
                    "idTeam": "133738",
                    "strTeam": "Real Madrid"
                }
            ]
        }

        # Mock eventslast response
        l_resp = MagicMock()
        l_resp.status_code = 200
        l_resp.json.return_value = {
            "results": [
                {
                    "strEvent": "Real Madrid vs Barcelona",
                    "strHomeTeam": "Real Madrid",
                    "strAwayTeam": "Barcelona",
                    "intHomeScore": "3",
                    "intAwayScore": "1",
                    "dateEvent": "2024-10-26",
                    "strLeague": "La Liga",
                    "strSport": "Soccer",
                    "strStatus": "FT"
                }
            ]
        }

        mock_get.side_effect = [t_resp, l_resp]

        res = self.service.fetch_sports_data("Real Madrid won yesterday's match", {})

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["sport"], "Football")
        self.assertEqual(res["matched_event"]["winner"], "Real Madrid")
        self.assertEqual(res["matched_event"]["home_score"], "3")
        self.assertEqual(res["matched_event"]["away_score"], "1")


if __name__ == "__main__":
    unittest.main()
