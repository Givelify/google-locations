"""module for unit testing"""

import unittest
from unittest.mock import MagicMock, patch

from requests import RequestException

from app.google_api_calls import _call_geocoding_api, geocoding_api_address


class TestApiFunctions(unittest.TestCase):
    """unit test class to test google api function calls"""

    @patch("app.google_api_calls._call_geocoding_api")
    def test_geocoding_api_address_success(self, mock__call_geocoding_api):
        """Test geocoding_api_address success"""
        address = "test_address"
        city = "test_city"
        state = "test_state"
        zipcode = "test_zip"
        country = "test_country"

        mock_response = MagicMock()
        mock__call_geocoding_api.return_value = mock_response

        response = geocoding_api_address(address, city, state, zipcode, country)

        mock__call_geocoding_api.assert_called_with(
            {
                "addressQuery": {
                    "addressQuery": f"{address}, {city}, {state} {zipcode}, {country}"
                }
            }
        )
        self.assertEqual(response, mock_response)

    @patch("app.google_api_calls.requests.post")
    def test_geocoding_api_success(self, mock_post):
        """Test _call_geocoding_api success"""
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
