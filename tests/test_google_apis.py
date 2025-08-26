"""module for unit testing"""

import unittest
from unittest.mock import MagicMock, patch

from requests.exceptions import RequestException

from app.google_api_calls import _call_geocoding_api, call_autocomplete, text_search
from app.models import GivingPartners


class TestApiFunctions(unittest.TestCase):
    """unit test class to test google api function calls"""

    @patch("app.google_api_calls.requests.post")
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

    @patch("app.google_api_calls.requests.post")
    def test_text_search_failure(self, mock_post):
        """Mock a failed response for text_search api call (non-200 status code)"""
        mock_response = MagicMock()
        mock_response.status_code.side_effect = [500, 429]
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

        text_search(gp_data)
        self.assertRaises(RequestException)
        # if a 429 occurs
        text_search(gp_data)
        self.assertRaises(RequestException)
        self.assertGreaterEqual(mock_post.call_count, 2)

    @patch("app.google_api_calls.requests.post")
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

    @patch("app.google_api_calls.requests.post")
    def test_call_autocomplete_failure(self, mock_post):
        """Mock a failed response for the autocomplete api call (non-200 status code)"""
        mock_response = MagicMock()
        mock_response.status_code.side_effect = [500, 429]
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

        call_autocomplete(gp_data)
        self.assertRaises(RequestException)
        # if a 429 occurs
        call_autocomplete(gp_data)
        self.assertRaises(RequestException)
        self.assertGreaterEqual(mock_post.call_count, 2)

    @patch("app.google_api_calls.requests.post")
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

    @patch("app.google_api_calls.requests.post")
    def test_geocoding_api_success(self, mock_post):
        """Mock the response from the geocoding_api api"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "address_components": [
                        {
                            "long_name": "707",
                            "short_name": "707",
                            "types": ["street_number"],
                        },
                        {
                            "long_name": "Collins Avenue",
                            "short_name": "Collins Ave",
                            "types": ["route"],
                        },
                        {
                            "long_name": "Ava",
                            "short_name": "Ava",
                            "types": ["locality", "political"],
                        },
                        {
                            "long_name": "Benton Township",
                            "short_name": "Benton Township",
                            "types": ["administrative_area_level_3", "political"],
                        },
                        {
                            "long_name": "Douglas County",
                            "short_name": "Douglas County",
                            "types": ["administrative_area_level_2", "political"],
                        },
                        {
                            "long_name": "Missouri",
                            "short_name": "MO",
                            "types": ["administrative_area_level_1", "political"],
                        },
                        {
                            "long_name": "United States",
                            "short_name": "US",
                            "types": ["country", "political"],
                        },
                        {
                            "long_name": "65608",
                            "short_name": "65608",
                            "types": ["postal_code"],
                        },
                    ],
                    "buildings": [
                        {
                            "building_outlines": [
                                {
                                    "display_polygon": {
                                        "type": "Polygon",
                                        "coordinates": [
                                            [
                                                [-92.6653733154025, 36.9425329312773],
                                                [-92.6656607099443, 36.9425568255168],
                                                [-92.6656936027867, 36.94230221016],
                                                [-92.6654060564636, 36.9422783192727],
                                                [-92.6653733154025, 36.9425329312773],
                                            ]
                                        ],
                                    }
                                }
                            ],
                            "place_id": "wiebiwebewfbweiqbfiq",
                        }
                    ],
                    "formatted_address": "707 Collins Ave, Ava, MO 65608, USA",
                    "geometry": {
                        "location": {"lat": 36.9424231, "lng": -92.6655258},
                        "location_type": "ROOFTOP",
                        "viewport": {
                            "northeast": {
                                "lat": 36.94376348029149,
                                "lng": -92.66406181970851,
                            },
                            "southwest": {
                                "lat": 36.94106551970849,
                                "lng": -92.66675978029151,
                            },
                        },
                    },
                    "navigation_points": [
                        {"location": {"latitude": 36.9424118, "longitude": -92.6653743}}
                    ],
                    "place_id": "wiebiwebewfbweiqbfiq",
                    "plus_code": {
                        "compound_code": "W8RM+XQ Ava, MO",
                        "global_code": "8689W8RM+XQ",
                    },
                    "types": [
                        "church",
                        "establishment",
                        "place_of_worship",
                        "point_of_interest",
                    ],
                }
            ],
            "status": "OK",
        }

        mock_post.return_value = mock_response

        place_id = "wiebiwebewfbweiqbfiq"
        data = {"place": f"places/{place_id}"}
        result = _call_geocoding_api(data)

        self.assertGreaterEqual(len(result), 1, "geocoding_api call success")
        self.assertEqual(
            result["results"][0]["buildings"][0]["place_id"],
            place_id,
        )

    @patch("app.google_api_calls.requests.post")
    def test_geocoding_api_failure(self, mock_post):
        """Mock a failed response for text_search api call (non-200 status code)"""
        mock_response = MagicMock()
        mock_response.status_code.side_effect = [500, 429]
        mock_response.text = "Error: Something went wrong"
        mock_post.return_value = mock_response

        place_id = "slfgrewoufewqifipew"
        data = {"place": f"places/{place_id}"}

        _call_geocoding_api(data)
        self.assertRaises(RequestException)
        # if a 429 occurs
        _call_geocoding_api(data)
        self.assertRaises(RequestException)
        self.assertGreaterEqual(mock_post.call_count, 2)


if __name__ == "__main__":
    unittest.main()
