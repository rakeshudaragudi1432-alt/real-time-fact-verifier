"""
Unit Tests for Science Service Module
"""

import unittest
from unittest.mock import patch, MagicMock
from services.science_service import ScienceService


class TestScienceService(unittest.TestCase):

    def setUp(self):
        self.service = ScienceService()

    def test_science_service_instantiation(self):
        self.assertIsNotNone(self.service)

    def test_empty_claim_returns_error(self):
        res = self.service.fetch_science_data("")
        self.assertEqual(res["status"], "error")

    def test_unrecognized_science_claim_returns_error(self):
        res = self.service.fetch_science_data("Xyz 12345 blorp non existent topic")
        self.assertEqual(res["status"], "error")

    @patch("services.science_service.requests.get")
    def test_mocked_wiki_science_fetch(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "title": "Moon",
            "extract": "The Moon is the only natural satellite of Earth.",
            "content_urls": {
                "desktop": {
                    "page": "https://en.wikipedia.org/wiki/Moon"
                }
            }
        }
        mock_get.return_value = mock_resp

        res = self.service.fetch_science_data("The Moon is Earth's natural satellite.")

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["topic"], "Moon")
        self.assertIn("natural satellite of Earth", res["extract"])
        self.assertEqual(res["source_url"], "https://en.wikipedia.org/wiki/Moon")


if __name__ == "__main__":
    unittest.main()
