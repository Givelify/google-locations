"""using sys module for importing modules from parent directory"""

import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.append("..")

from google_api_calls import (  # pylint: disable=wrong-import-position
    call_autocomplete,
    text_search,
)


class TestApiFunctions(unittest.TestCase):
    """unit test class to test google api function calls"""

    @patch("requests.post")
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

        # Sample data to pass into the function
        gp_data = {
            "name": "Test Place",
            "city": "test city",
            "state": "Test State",
        }

        # Run the text_search function
        result = text_search(gp_data)

        # Check that the result matches the expected output
        self.assertGreaterEqual(len(result), 1, "text_search call success")
        self.assertEqual(
            result[0]["formattedAddress"], "484 test Rd, test city, TS 45678, USA"
        )

    @patch("requests.post")
    def test_text_search_failure(self, mock_post):
        """Mock a failed response for text_search api call (non-200 status code)"""
        mock_response = MagicMock()
        mock_response.status_code = 500  # Internal Server Error
        mock_response.text = "Error: Something went wrong"
        mock_post.return_value = mock_response

        gp_data = {
            "name": "Test Place",
            "city": "test city",
            "state": "Test State",
        }

        # Run the text_search function
        result = text_search(gp_data)

        # Assert that the result is None when the API fails
        self.assertIsNone(result)

    @patch("requests.post")
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

        # Sample data to pass into the function
        gp_data = {"name": "Test church", "donee_lat": 40.7128, "donee_lon": -74.0060}

        # Run the call_autocomplete function
        result = call_autocomplete(gp_data)

        # Check that the result contains the expected data
        self.assertEqual(
            result["suggestions"][0]["placePrediction"]["structuredFormat"][
                "secondaryText"
            ]["text"],
            "West test Drive, test city, TS, USA",
        )

    @patch("requests.post")
    def test_call_autocomplete_failure(self, mock_post):
        """Mock a failed response for the autocomplete api call (non-200 status code)"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Error: Something went wrong"
        mock_post.return_value = mock_response

        gp_data = {"name": "Test Place", "donee_lat": 40.7128, "donee_lon": -74.0060}

        # Run the call_autocomplete function
        result = call_autocomplete(gp_data)

        # Assert that the result is None when the API fails
        self.assertIsNone(result)

    @patch("requests.post")
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

        # Sample data to pass into the function (no location bias)
        gp_data = {"name": "Test Place", "donee_lat": 0, "donee_lon": 0}

        # Run the call_autocomplete function
        result = call_autocomplete(gp_data)

        # Check that the result is as expected
        self.assertEqual(
            result["suggestions"][0]["placePrediction"]["structuredFormat"][
                "secondaryText"
            ]["text"],
            "West test Drive, test city, TS, USA",
        )


if __name__ == "__main__":
    unittest.main()
