"""using sys module for importing modules from parent directory"""

import sys
import unittest
from unittest.mock import patch

sys.path.append("..")

from checks import autocomplete_check, fuzzy_address_check, normalize_address


class TestChecks(unittest.TestCase):
    def test_normalize_address(self):
        self.assertEqual(normalize_address("United States"), "usa")
        self.assertEqual(normalize_address("Bahamas"), "bahamas")
        self.assertEqual(normalize_address("US"), "usa")
        self.assertEqual(normalize_address("U.S.A."), "usa")
        self.assertEqual(normalize_address("U.S."), "usa")
        self.assertEqual(normalize_address("U.S"), "usa")
        self.assertEqual(normalize_address("U.S.A"), "usa")
        self.assertEqual(normalize_address("America"), "usa")

    @patch("checks.fuzz.ratio", return_value=95)
    def test_fuzzy_address_check(self, mock_ratio):
        api_address = "123 Main St, Springfield, IL, USA"
        gp_address = "123 Main Street, Springfield, Illinois, USA"
        result = fuzzy_address_check(api_address, gp_address)
        self.assertTrue(result)
        mock_ratio.assert_called_once()

    @patch(
        "checks.call_autocomplete",
        return_value={
            "suggestions": [
                {
                    "placePrediction": {
                        "place": "places/place1_id",
                        "placeId": "place1_id",
                        "text": {
                            "text": "test Church, 123 Main St, Springfield, IL, USA",
                            "matches": [{"endOffset": 37}],
                        },
                        "structuredFormat": {
                            "mainText": {
                                "text": "test Church",
                                "matches": [{"endOffset": 37}],
                            },
                            "secondaryText": {
                                "text": "123 Main St, Springfield, IL, USA"
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
    @patch("checks.fuzzy_address_check", return_value=True)
    def test_autocomplete_check(self, mock_fuzzy_check, mock_autocomplete):
        donee_info_gp = {
            "name": "Test GP",
            "address": "123 Main St",
            "city": "Springfield",
            "state": "IL",
            "country": "USA",
        }
        result = autocomplete_check(donee_info_gp)
        self.assertTrue(result)
        mock_autocomplete.assert_called_once_with(donee_info_gp)
        mock_fuzzy_check.assert_called_once()


if __name__ == "__main__":
    unittest.main()
