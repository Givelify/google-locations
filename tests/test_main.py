"""sys module for accessing modules in parent directory"""

import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy import Column, Float, Integer, MetaData, String, Table, create_engine

import main


class TestGPProcessor(unittest.TestCase):
    """testing class for main.py"""

    @patch("main.process_gp")
    def test_main_select_query_with_one_row(self, mock_process_gp):
        """unit test to check whether the select query works or not"""
        engine = create_engine("sqlite:///:memory:")
        metadata = MetaData()

        donee_info = Table(
            "donee_info",
            metadata,
            Column("donee_id", Integer, primary_key=True),
            Column("name", String),
            Column("address", String),
            Column("city", String),
            Column("state", String),
            Column("country", String),
            Column("active", Integer),
            Column("unregistered", Integer),
        )

        giving_partner_locations = Table(
            "giving_partner_locations",
            metadata,
            Column("giving_partner_id", Integer, primary_key=True),
            schema=None,
        )

        metadata.create_all(engine)

        with engine.begin() as conn:
            conn.execute(
                donee_info.insert(),
                {
                    "donee_id": 1,
                    "name": "Test Org",
                    "address": "123 Main St",
                    "city": "Metropolis",
                    "state": "CA",
                    "country": "USA",
                    "active": 1,
                    "unregistered": 0,
                },
            )

        with patch("main.create_engine", return_value=engine), patch(
            "main.Table",
            side_effect=lambda name, *a, **k: (
                donee_info if name == "donee_info" else giving_partner_locations
            ),
        ):
            main.main()

        mock_process_gp.assert_called_once()
        row_data = mock_process_gp.call_args[0][0]
        self.assertEqual(row_data["donee_id"], 1)
        self.assertEqual(row_data["country"], "USA")

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

        mock_autocomplete.return_value = (False, None)
        mock_text_search.return_value = []
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
