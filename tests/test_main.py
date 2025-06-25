"""unitest module for testing"""

import unittest
from unittest.mock import MagicMock, patch

import main
from models import GivingPartners


class TestGPProcessor(unittest.TestCase):
    """testing class for main.py"""

    @patch("main.get_engine")
    @patch("main.get_session")
    def test_main(self, mock_get_session, mock_get_engine):
        """unit test to check whether the select query works or not"""
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_result = MagicMock()

        mock_row = MagicMock()
        mock_row.id = "1"
        mock_result.all.return_value = [mock_row]
        mock_session.scalars.return_value = mock_result

    @patch("main.get_session")
    @patch("main.autocomplete_check")
    def test_process_gp_autocomplete_success(self, mock_autocomplete, mock_get_session):
        """testing funciton for cases with a passing autocomplete check"""
        mock_gp = GivingPartners(
            name="Test Church",
            city="Testville",
            state="TS",
            address="123 Test St",
            latitude=12.34,
            longitude=56.78,
            phone="2345756757",
            country="USA",
            zip="34567",
            active=1,
            unregistered=0,
            id=1,
        )

        # Mock a successful autocomplete check
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        mock_autocomplete.return_value = "place_id_123"

        main.process_gp(mock_gp, mock_session)
        print(mock_session.add.call_args[0][0].api_id)
        self.assertEqual(
            mock_session.add.call_args[0][0].address,
            f"{mock_gp.address}, {mock_gp.city}, {mock_gp.state}, {mock_gp.country}",
        )
        mock_session.commit.assert_called_once()

    @patch("main.get_session")
    @patch("main.autocomplete_check")
    @patch("main.text_search")
    def test_process_gp_text_search_success(
        self, mock_text_search, mock_autocomplete, mock_get_session
    ):
        """testing function for cases with failure of autocomplete check and text search api success"""  # pylint: disable=line-too-long
        mock_gp = GivingPartners(
            name="Faith Center",
            city="Hope City",
            state="HC",
            address="456 Hope Rd",
            latitude=34.56,
            longitude=78.90,
            phone="9876543210",
            country="USA",
            zip="45678",
            active=1,
            unregistered=0,
            id=2,
        )

        mock_autocomplete.return_value = None
        mock_top_result = {
            "displayName": {"text": "Faith Center"},
            "formattedAddress": "123 test Rd, Hope City, HC, USA",
            "location": {"latitude": 55.66, "longitude": 33.45},
            "id": "api_id_456",
        }
        mock_text_search.return_value = [mock_top_result]

        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        main.process_gp(mock_gp, mock_session)
        print(mock_session.add.call_args[0][0].address)
        self.assertEqual(
            mock_session.add.call_args[0][0].address,
            mock_top_result["formattedAddress"],
        )
        mock_session.commit.assert_called_once()

    @patch("main.get_session")
    @patch("main.autocomplete_check")
    @patch("main.text_search")
    def test_process_gp_no_hits(
        self, mock_text_search, mock_autocomplete, mock_get_session
    ):
        """testing funciton for cases with autcomplete check fail, and no hits for text search api call"""  # pylint: disable=line-too-long
        mock_gp = GivingPartners(
            name="Grace Hall",
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

        mock_autocomplete.return_value = None
        mock_text_search.return_value = []
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        main.process_gp(mock_gp, mock_session)
        mock_session.add.assert_not_called()

    @patch("main.get_session")
    @patch("main.autocomplete_check")
    @patch("main.text_search")
    def test_process_gp_failure_on_hit(
        self, mock_text_search, mock_autocomplete, mock_get_session
    ):
        """testing function for cases of autocomplete check fail, and the topmost hit of text search api not matching gp from donee_info table"""  # pylint: disable=line-too-long
        mock_gp = GivingPartners(
            name="Grace Hall",
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

        mock_autocomplete.return_value = None
        mock_top_result = {
            "displayName": {"text": "Grace banquet center"},
            "formattedAddress": "123 test Rd, test City, TS, USA",
            "location": {"latitude": 45.67, "longitude": 34.67},
            "id": "api_id_456",
        }
        mock_text_search.return_value = [mock_top_result]
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        main.process_gp(mock_gp, mock_session)

        mock_session.add.assert_not_called()


if __name__ == "__main__":
    unittest.main()
