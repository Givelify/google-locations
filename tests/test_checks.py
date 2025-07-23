"""using sys module for importing modules from parent directory"""

import unittest
from unittest.mock import patch

from checks import (
    autocomplete_check,
    fuzzy_address_check,
    normalize_address,
    text_search_similarity_check,
)
from models import GivingPartners


class TestChecks(unittest.TestCase):
    """Unit tests for the checks module"""

    @patch("checks.fuzz.ratio", return_value=95)
    def test_text_search_similarity_check(
        self,
        mock_ratio,
    ):
        """Test the text_search_similarity_check function"""
        topmost = {
            "displayName": {"text": "test GP"},
            "placeId": "place1_id",
            "formattedAddress": "889 West blvd, Peaceville, PV, USA, 45688",
        }
        donee_info_gp = GivingPartners(
            name="test gp",
            id=3,
        )

        result = text_search_similarity_check(donee_info_gp, topmost)
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
    @patch("checks.fuzz.ratio")
    def test_fuzzy_address_check(
        self,
        mock_fuzz_ratio,
        mock_normalize_address,
    ):
        """Test fuzzy_address_check"""
        mock_normalize_address.side_effect = [
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
        gp_address = "123 Main Street, Springfield, Illinois, USA"
        api_address = "123 Main St, Springfield, Illinois, USA"
        result = fuzzy_address_check(api_address, gp_address)
        self.assertEqual(result, 95)

    @patch("checks.normalize_address")
    @patch("checks.fuzz.ratio")
    def test_fuzzy_address_check_exception(
        self,
        mock_fuzz_ratio,
        mock_normalize_address,
    ):
        """Test fuzzy_address_check exception"""
        mock_normalize_address.side_effect = Exception
        api_address1 = "123 M St, Springfield, USA"
        gp_address1 = "123 Main Street, Springfield, Illinois, USA"
        with self.assertRaises(Exception):
            fuzzy_address_check(api_address1, gp_address1)
        mock_fuzz_ratio.assert_not_called()

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
        mock_fuzzy_address_check.side_effect = [92, 60, 60]

        giving_partner = GivingPartners(
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
        result = autocomplete_check(giving_partner)
        mock_call_autocomplete.assert_called_with(giving_partner)
        self.assertEqual(result, "place1_id")

        giving_partner_2 = GivingPartners(
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
        result2 = autocomplete_check(giving_partner_2)
        mock_call_autocomplete.assert_called_with(giving_partner_2)
        self.assertIsNone(result2)

        giving_partner_3 = GivingPartners(
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
        result3 = autocomplete_check(giving_partner_3)
        mock_call_autocomplete.assert_called_with(giving_partner_3)
        self.assertIsNone(result3)


if __name__ == "__main__":
    unittest.main()
