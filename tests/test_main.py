"""sys module for accessing modules in parent directory"""

import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy import Column, Float, Integer, MetaData, String, Table

import main


class TestGPProcessor(unittest.TestCase):
    """testing class for process_gp function"""

    @patch("main.autocomplete_check")
    def test_process_gp_autocomplete_success(self, mock_autocomplete):
        """testing funciton for cases with a passing autocomplete check"""
        mock_gp = {
            "donee_id": 1,
            "name": "Test Church",
            "address": "123 Test St",
            "city": "Testville",
            "state": "TS",
            "country": "USA",
            "phone": "1234567890",
            "donee_lat": 12.34,
            "donee_lon": 56.78,
        }

        # Mock a successful autocomplete check
        mock_autocomplete.return_value = (True, "place_id_123")
        metadata = MetaData()
        mock_table = Table(
            "giving_partners",
            metadata,
            Column("giving_partner_id", Integer),
            Column("name", String),
            Column("address", String),
            Column("city", String),
            Column("state", String),
            Column("country", String),
            Column("phone_number", String),
            Column("latitude", Float),
            Column("longitude", Float),
            Column("api_id", String),
            Column("source", String),
        )
        mock_connection = MagicMock()

        result = main.process_gp(mock_gp, mock_connection, mock_table)

        self.assertTrue(result)
        mock_connection.execute.assert_called_once()
        args, _ = mock_connection.execute.call_args
        params = args[0].compile().params
        self.assertEqual(params["api_id"], "place_id_123")

    @patch("main.autocomplete_check")
    @patch("main.text_search")
    def test_process_gp_text_search_success(self, mock_text_search, mock_autocomplete):
        """testing function for cases with failure of autocomplete check and text search api success"""  # pylint: disable=line-too-long
        mock_gp = {
            "donee_id": 2,
            "name": "Faith Center",
            "address": "456 Hope Rd",
            "city": "Hope City",
            "state": "HC",
            "country": "USA",
            "phone": "9876543210",
            "donee_lat": 34.56,
            "donee_lon": 78.90,
        }

        # Simulate failed autocomplete, fallback to text search
        mock_autocomplete.return_value = (False, None)
        mock_top_result = {
            "displayName": {"text": "Faith Center"},
            "formattedAddress": "456 Hope Rd, Hope City, HC, USA",
            "location": {"latitude": 34.56, "longitude": 78.90},
            "id": "api_id_456",
        }
        mock_text_search.return_value = [mock_top_result]

        metadata = MetaData()
        mock_table = Table(
            "giving_partners",
            metadata,
            Column("giving_partner_id", Integer),
            Column("name", String),
            Column("address", String),
            Column("city", String),
            Column("state", String),
            Column("country", String),
            Column("phone_number", String),
            Column("latitude", Float),
            Column("longitude", Float),
            Column("api_id", String),
            Column("source", String),
        )
        mock_connection = MagicMock()
        result = main.process_gp(mock_gp, mock_connection, mock_table)

        self.assertTrue(result)
        mock_connection.execute.assert_called_once()
        args, _ = mock_connection.execute.call_args
        params = args[0].compile().params
        self.assertEqual(params["api_id"], "api_id_456")

    @patch("main.autocomplete_check")
    @patch("main.text_search")
    def test_process_gp_no_hits(self, mock_text_search, mock_autocomplete):
        """testing funciton for cases with autcomplete check fail, and no hits for text search api call"""  # pylint: disable=line-too-long
        mock_gp = {
            "donee_id": 3,
            "name": "Grace Hall",
            "address": "789 Peace Ave",
            "city": "Peaceville",
            "state": "PV",
            "country": "USA",
            "phone": "1231231234",
            "donee_lat": 90.00,
            "donee_lon": 45.00,
        }

        # Both autocomplete and text search fail
        mock_autocomplete.return_value = (False, None)
        mock_text_search.return_value = []  # no hits for text search api call
        mock_connection = MagicMock()
        mock_table = MagicMock(spec=Table)

        result = main.process_gp(mock_gp, mock_connection, mock_table)

        self.assertFalse(result)
        mock_connection.execute.assert_not_called()

    @patch("main.autocomplete_check")
    @patch("main.text_search")
    def test_process_gp_failure_on_hit(self, mock_text_search, mock_autocomplete):
        """testing function for cases of autocomplete check fail, and the topmost hit of text search api not matching gp from donee_info table"""  # pylint: disable=line-too-long
        mock_gp = {
            "donee_id": 3,
            "name": "Grace Hall",
            "address": "789 Peace Ave",
            "city": "Peaceville",
            "state": "PV",
            "country": "USA",
            "phone": "1231231234",
            "donee_lat": 90.00,
            "donee_lon": 45.00,
        }

        # Both autocomplete and text search fail
        mock_autocomplete.return_value = (False, None)
        mock_top_result = {
            "displayName": {"text": "Grace center"},
            "formattedAddress": "466 test Rd, test City, TS, USA",
            "location": {"latitude": 45.67, "longitude": 34.67},
            "id": "api_id_456",
        }
        mock_text_search.return_value = [mock_top_result]
        mock_connection = MagicMock()
        mock_table = MagicMock(spec=Table)

        result = main.process_gp(mock_gp, mock_connection, mock_table)

        self.assertFalse(result)
        mock_connection.execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
