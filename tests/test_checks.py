"""using sys module for importing modules from parent directory"""

import sys
import unittest
from unittest.mock import patch

sys.path.append("..")

from checks import (
    autocomplete_check,
    check_topmost,
    fuzzy_address_check,
    normalize_address,
)


class TestChecks(unittest.TestCase):
    """Unit tests for the checks module"""

    # write a unit test for the below function
    @patch("checks.fuzz.ratio", return_value=95)
    def test_check_topmost(self, mock_ratio):
        """Test the check_topmost function"""
        topmost = {
            "displayName": {"text": "test GP"},
            "placeId": "place1_id",
        }
        donee_info_gp = {"name": "Test gp"}
        result = check_topmost(topmost, donee_info_gp)
        self.assertTrue(result)
        mock_ratio.assert_called_once_with("test gp", "test gp")

    def test_normalize_address(self):
        """Test the normalize_address function"""
        self.assertEqual(
            normalize_address("630 W 28th St, Indianapolis, IN, United States")[
                "country"
            ],
            "usa",
        )
        self.assertEqual(
            normalize_address("Columbus Dr & Nansen Ave, Freeport, GBI, BHS")[
                "country"
            ],
            "bahamas",
        )
        self.assertEqual(
            normalize_address("630 W 28th St, Indianapolis, IN, US")["country"],
            "usa",
        )
        self.assertEqual(
            normalize_address("630 W 28th St, Indianapolis, IN, U.S.A.")["country"],
            "usa",
        )
        self.assertEqual(
            normalize_address("630 W 28th St, Indianapolis, IN, U.S.")["country"],
            "usa",
        )
        self.assertEqual(
            normalize_address("630 W 28th St, Indianapolis, IN, U.S")["country"],
            "usa",
        )
        self.assertEqual(
            normalize_address("630 W 28th St, Indianapolis, IN, U.S.A")["country"],
            "usa",
        )
        self.assertEqual(
            normalize_address("630 W 28th St, Indianapolis, IN, America")["country"],
            "usa",
        )

        expected_dict = {
            "street": "630 w 28th st, test lane, test blvd",
            "city": "indianapolis",
            "state": "in",
            "country": "usa",
        }
        self.assertEqual(
            normalize_address(
                "630 W 28th St, test lane, test blvd, Indianapolis, IN, America"
            ),
            expected_dict,
        )

        with self.assertRaises(Exception):
            normalize_address("630 W 28th St, IN, America")

    # @patch("checks.fuzz.ratio", return_value=95)
    def test_fuzzy_address_check(self):
        """Test the fuzzy_address_check function"""
        api_address1 = "123 Main St, Springfield, USA"
        gp_address1 = "123 Main Street, Springfield, Illinois, USA"
        with self.assertRaises(Exception):
            fuzzy_address_check(api_address1, gp_address1)
        api_address2 = "123 Main St, Springfield, Illinois, USA"
        self.assertTrue(fuzzy_address_check(api_address2, gp_address1))
        # mock_ratio.assert_called_once()

    @patch(
        "checks.call_autocomplete",
        return_value={
            "suggestions": [
                {
                    "placePrediction": {
                        "place": "places/place1_id",
                        "placeId": "place1_id",
                        "text": {
                            "text": "test GP, West Strieff Lane, Glenwood, IL, USA",
                            "matches": [{"endOffset": 37}],
                        },
                        "structuredFormat": {
                            "mainText": {
                                "text": "test GP",
                                "matches": [{"endOffset": 37}],
                            },
                            "secondaryText": {
                                "text": "West Strieff Lane, Glenwood, IL, USA"
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
        },
    )
    # @patch("checks.fuzzy_address_check", return_value=True)
    def test_autocomplete_check_success(self, mock_call_autocomplete):
        """Test the autocomplete_check function"""
        donee_info_gp = {
            "name": "Test GP",
            "address": "845 W Strieff Ln",
            "city": "Glenwood",
            "state": "IL",
            "country": "United States",
        }
        result = autocomplete_check(donee_info_gp)
        self.assertTupleEqual(result, (True, "place1_id"))

        donee_info_gp2 = {
            "name": "Test GP",
            "address": "845 Bakers Ln",
            "city": "Glenwood",
            "state": "IL",
            "country": "United States",
        }
        result2 = autocomplete_check(donee_info_gp2)
        self.assertTupleEqual(result2, (False, ""))

        donee_info_gp3 = {
            "name": "Test GP",
            "address": "845 Bakers Ln",
            "city": "",
            "state": "IL",
            "country": "United States",
        }
        result3 = autocomplete_check(donee_info_gp3)
        self.assertTupleEqual(result3, (False, ""))


if __name__ == "__main__":
    unittest.main()
