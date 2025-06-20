"""using sys module for importing modules from parent directory"""

import unittest
from unittest.mock import MagicMock, patch

from google_api_calls import call_autocomplete, text_search
from models import GivingPartners


class TestApiFunctions(unittest.TestCase):
    """unit test class to test google api function calls"""

    @patch("google_api_calls.requests.post")
    def test_text_search_success(self, mock_post):
        """Mock the response from the text_search api"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "places": [
                {
                    "id": "xyztycfytui",
                    "formattedAddress": "484 test Rd, test city, TS 45678, USA",
                    "location": {
                        "latitude": 34.4254524,
                        "longitude": -42.43554,
                    },
                    "displayName": {
                        "text": "testing church",
                        "languageCode": "en",
                    },
                    "shortFormattedAddress": "484 test Rd, test city",
                }
            ]
        }
        mock_post.return_value = mock_response

        gp_data = GivingPartners(
            name="Test Place",
            city="test city",
            state="Test State",
            address="484 test Rd",
            latitude=34.4254524,
            longitude=-42.43554,
            phone="123-456-7890",
            country="USA",
            zip="45678",
            active=1,
            unregistered=0,
            id=1,
        )
        result = text_search(gp_data)

        self.assertGreaterEqual(len(result), 1, "text_search call success")
        self.assertEqual(
            result[0]["formattedAddress"], "484 test Rd, test city, TS 45678, USA"
        )

    @patch("google_api_calls.requests.post")
    def test_text_search_failure(self, mock_post):
        """Mock a failed response for text_search api call (non-200 status code)"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Error: Something went wrong"
        mock_post.return_value = mock_response

        gp_data = GivingPartners(
            name="Test Place",
            city="test city",
            state="Test State",
            address="484 test Rd",
            latitude=34.4254524,
            longitude=-42.43554,
            phone="123-456-7890",
            country="USA",
            zip="45678",
            active=1,
            unregistered=0,
            id=1,
        )

        result = text_search(gp_data)
        self.assertIsNone(result)

    @patch("google_api_calls.requests.post")
    def test_call_autocomplete_success(self, mock_post):
        """Mock the response for the autocomplete api call"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "suggestions": [
                {
                    "placePrediction": {
                        "place": "places/place1_id",
                        "placeId": "place1_id",
                        "text": {
                            "text": "test Church, West test Drive, test city, TS, USA",
                            "matches": [{"endOffset": 37}],
                        },
                        "structuredFormat": {
                            "mainText": {
                                "text": "test Church",
                                "matches": [{"endOffset": 37}],
                            },
                            "secondaryText": {
                                "text": "West test Drive, test city, TS, USA"
                            },
                        },
                        "types": [
                            "place_of_worship",
                            "establishment",
                            "point_of_interest",
                        ],
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        gp_data = GivingPartners(
            name="Test Place",
            city="test city",
            state="Test State",
            address="484 test Rd",
            latitude=34.4254524,
            longitude=-42.43554,
            phone="123-456-7890",
            country="USA",
            zip="45678",
            active=1,
            unregistered=0,
            id=1,
        )
        result = call_autocomplete(gp_data)

        self.assertEqual(
            result["suggestions"][0]["placePrediction"]["structuredFormat"][
                "secondaryText"
            ]["text"],
            "West test Drive, test city, TS, USA",
        )

    @patch("google_api_calls.requests.post")
    def test_call_autocomplete_failure(self, mock_post):
        """Mock a failed response for the autocomplete api call (non-200 status code)"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Error: Something went wrong"
        mock_post.return_value = mock_response

        gp_data = GivingPartners(
            name="Test Place",
            city="test city",
            state="Test State",
            address="484 test Rd",
            latitude=34.4254524,
            longitude=-42.43554,
            phone="123-456-7890",
            country="USA",
            zip="45678",
            active=1,
            unregistered=0,
            id=1,
        )

        result = call_autocomplete(gp_data)

        self.assertIsNone(result)

    @patch("google_api_calls.requests.post")
    def test_call_autocomplete_with_no_location_bias(self, mock_post):
        """Mock a success response for the autocomplete api when gp doesnt have lat / long in the database"""  # pylint: disable=line-too-long
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "autocomplete call without location bias success"
        mock_response.json.return_value = {
            "suggestions": [
                {
                    "placePrediction": {
                        "place": "places/place1_id",
                        "placeId": "place1_id",
                        "text": {
                            "text": "test Church, West test Drive, test city, TS, USA",
                            "matches": [{"endOffset": 37}],
                        },
                        "structuredFormat": {
                            "mainText": {
                                "text": "test Church",
                                "matches": [{"endOffset": 37}],
                            },
                            "secondaryText": {
                                "text": "West test Drive, test city, TS, USA"
                            },
                        },
                        "types": [
                            "place_of_worship",
                            "establishment",
                            "point_of_interest",
                        ],
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        gp_data = GivingPartners(
            name="Test Place",
            city="test city",
            state="Test State",
            address="484 test Rd",
            latitude=0,
            longitude=0,
            phone="123-456-7890",
            country="USA",
            zip="45678",
            active=1,
            unregistered=0,
            id=1,
        )

        result = call_autocomplete(gp_data)

        self.assertEqual(
            result["suggestions"][0]["placePrediction"]["structuredFormat"][
                "secondaryText"
            ]["text"],
            "West test Drive, test city, TS, USA",
        )


if __name__ == "__main__":
    unittest.main()
