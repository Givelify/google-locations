"""using sys module for importing modules from parent directory"""

import unittest
from unittest.mock import patch

from checks import (autocomplete_check, check_topmost, fuzzy_address_check,
                    normalize_address)
from models import GivingPartners


class TestChecks(unittest.TestCase):
    """Unit tests for the checks module"""

    @patch("checks.fuzz.ratio", return_value=95)
    def test_check_topmost(self, mock_ratio):
        """Test the check_topmost function"""
        topmost = {
            "displayName": {"text": "test GP"},
            "placeId": "place1_id",
            "formattedAddress": "889 West blvd, Peaceville, PV, USA, 45688",
        }
        donee_info_gp = GivingPartners(
            name="test gp",
            city="Peaceville",
            state="PV",
            address="789 Peace Ave",
            latitude=90.00,
            longitude=45.00,
            phone="1231231234",
            country="USA",
            zip="45678",
            active=1,
            unregistered=0,
            id=3,
        )
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

    @patch("checks.normalize_address")
    @patch("rapidfuzz.fuzz.ratio")
    def test_fuzzy_address_check(self, mock_fuzz_ratio, mock_normalize_address):
        """Test the fuzzy_address_check function"""
        mock_normalize_address.side_effect = [
            Exception,
            {
                "street": "123 M St",
                "country": "USA",
                "state": "Illinois",
                "city": "Springfield",
            },
            {
                "street": "123 Main Street",
                "country": "USA",
                "state": "Illinois",
                "city": "Springfield",
            },
        ]
        mock_fuzz_ratio.side_effect = [90, 100, 100, 100]
        api_address1 = "123 M St, Springfield, USA"
        gp_address1 = "123 Main Street, Springfield, Illinois, USA"
        with self.assertRaises(Exception):
            fuzzy_address_check(api_address1, gp_address1)
        api_address2 = "123 Main St, Springfield, Illinois, USA"
        self.assertEqual(fuzzy_address_check(api_address2, gp_address1), 95)

    @patch("checks.fuzzy_address_check")
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
    def test_autocomplete_check_success(
        self, mock_call_autocomplete, mock_fuzzy_address_check
    ):  # pylint: disable=unused-argument
        """Test the autocomplete_check function success"""
        donee_info_gp = GivingPartners(
            name="Test GP",
            city="Glenwood",
            state="IL",
            address="845 W Strieff Ln",
            latitude=90.00,
            longitude=45.00,
            phone="1231231234",
            country="United States of America",
            zip="45678",
            active=1,
            unregistered=0,
            id=3,
        )
        mock_fuzzy_address_check.side_effect = [82, 60, 60]
        result = autocomplete_check(donee_info_gp)
        self.assertEqual(result, "place1_id")

        donee_info_gp2 = GivingPartners(
            name="Test GP",
            city="Glenwood",
            state="IL",
            address="845 Bakers Ln",
            latitude=90.00,
            longitude=45.00,
            phone="1231231234",
            country="United States",
            zip="45678",
            active=1,
            unregistered=0,
            id=3,
        )
        result2 = autocomplete_check(donee_info_gp2)
        self.assertIsNone(result2)

        donee_info_gp3 = GivingPartners(
            name="Test GP",
            city="",
            state="IL",
            address="845 Bakers Ln",
            latitude=90.00,
            longitude=45.00,
            phone="1231231234",
            country="United States",
            zip="45678",
            active=1,
            unregistered=0,
            id=3,
        )
        result3 = autocomplete_check(donee_info_gp3)
        self.assertIsNone(result3)


if __name__ == "__main__":
    unittest.main()
