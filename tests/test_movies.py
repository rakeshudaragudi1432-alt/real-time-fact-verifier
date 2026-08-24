"""
Unit Tests for Movie Service Module
"""

import unittest
from unittest.mock import patch, MagicMock
from services.movie_service import MovieService


class TestMovieService(unittest.TestCase):

    def setUp(self):
        self.service = MovieService()

    def test_movie_service_instantiation(self):
        self.assertIsNotNone(self.service)

    def test_empty_claim_returns_error(self):
        res = self.service.fetch_movie_info("", {})
        self.assertEqual(res["status"], "error")
        self.assertIn("Invalid claim text input", res["error_message"])

    def test_no_movie_found_returns_error(self):
        res = self.service.fetch_movie_info("A random phrase without any movie title Xyz123")
        self.assertEqual(res["status"], "error")

    @patch("services.movie_service.requests.get")
    def test_mocked_successful_omdb_fetch(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "Response": "True",
            "Title": "Interstellar",
            "Year": "2014",
            "Released": "07 Nov 2014",
            "Director": "Christopher Nolan",
            "Actors": "Matthew McConaughey, Anne Hathaway, Jessica Chastain",
            "Genre": "Adventure, Drama, Sci-Fi",
            "imdbRating": "8.7",
            "Runtime": "169 min",
            "Plot": "A team of explorers travel through a wormhole in space."
        }
        mock_get.return_value = mock_resp

        res = self.service.fetch_movie_info("Interstellar was released in 2014")

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["title"], "Interstellar")
        self.assertEqual(res["year"], "2014")
        self.assertEqual(res["director"], "Christopher Nolan")
        self.assertEqual(res["rating"], 8.7)


if __name__ == "__main__":
    unittest.main()
