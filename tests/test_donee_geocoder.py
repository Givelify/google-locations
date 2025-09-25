"""unitest module for testing"""

import unittest
from unittest.mock import MagicMock, call, patch

from app.scripts.donee_geocoder import main
from app.services.location_and_outlines import (
    process_location_and_outlines,
    run_location_and_outlines,
)


class TestDoneeGeocoder(unittest.TestCase):
    """testing class for donee_geocoder.py"""

    @patch("app.scripts.donee_geocoder.get_engine")
    @patch("app.scripts.donee_geocoder.get_session")
    @patch("app.scripts.donee_geocoder.run_location_and_outlines")
    def test_main_donee_geocoder(
        self,
        mock_run_location_and_outlines,
        mock_get_session,
        mock_get_engine,
    ):
        """Test main() donee_geocoder flow"""
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine

        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        main()

        mock_run_location_and_outlines.assert_called_with(mock_session)

    @patch("app.services.location_and_outlines.process_location_and_outlines")
    @patch("app.services.location_and_outlines.get_giving_partners")
    def test_run_location_and_outlines(
        self,
        mock_get_giving_partners,
        mock_process_location_and_outlines,
    ):
        """Test run_location_and_outlines() success flow"""
        mock_session = MagicMock()

        mock_gp_1 = MagicMock()
        mock_gp_1.id = 1
        mock_gp_2 = MagicMock()
        mock_gp_2.id = 2
        mock_get_giving_partners.return_value = [mock_gp_1, mock_gp_2]

        run_location_and_outlines(mock_session)
        mock_get_giving_partners.assert_called_with(mock_session)
        mock_process_location_and_outlines.assert_has_calls(
            [
                call(mock_session, mock_gp_1),
                call(mock_session, mock_gp_2),
            ]
        )

    @patch("app.services.location_and_outlines.process_location_and_outlines")
    @patch("app.services.location_and_outlines.get_giving_partners")
    def test_run_location_and_outlines_no_gps(
        self,
        mock_get_giving_partners,
        mock_process_location_and_outlines,
    ):
        """Test run_location_and_outlines() no giving partners"""
        mock_session = MagicMock()
        mock_get_giving_partners.return_value = []

        run_location_and_outlines(mock_session)
        mock_get_giving_partners.assert_called_with(mock_session)
        mock_process_location_and_outlines.assert_not_called()

    @patch("app.services.location_and_outlines.geocoding_api_address")
    @patch("app.services.location_and_outlines.extract_building_polygons")
    @patch("app.services.location_and_outlines.get_lat_lon")
    @patch("app.services.location_and_outlines.insert_google_data")
    def test_process_location_and_outlines(
        self,
        mock_insert_google_data,
        mock_get_lat_lon,
        mock_extract_building_polygons,
        mock_geocoding_api_address,
    ):
        """process_location_and_outlines autocomplete"""
        mock_gp = MagicMock()
        mock_gp.donee_id = 1
        mock_gp.address = "test_address"
        mock_gp.city = "test_city"
        mock_gp.state = "test_state"
        mock_gp.zip = "test_zip"
        mock_gp.country = "test_country"

        mock_session = MagicMock()
        mock_geocoding_results = {"destinations": [{MagicMock()}]}
        mock_geocoding_api_address.return_value = mock_geocoding_results
        mock_building_outlines = [{MagicMock()}]
        mock_extract_building_polygons.return_value = mock_building_outlines
        mock_get_lat_lon.return_value = (10, 10)

        process_location_and_outlines(mock_session, mock_gp)
        mock_geocoding_api_address.assert_called_with(
            "test_address",
            "test_city",
            "test_state",
            "test_zip",
            "test_country",
        )
        mock_insert_google_data.assert_called_with(
            mock_session, mock_gp, 10, 10, mock_building_outlines
        )

    @patch("app.services.location_and_outlines.geocoding_api_address")
    @patch("app.services.location_and_outlines.insert_google_data")
    def test_process_location_and_outlines_no_results(
        self,
        mock_insert_google_data,
        mock_geocoding_api_address,
    ):
        """process_location_and_outlines where no results"""
        mock_gp = MagicMock()
        mock_gp.donee_id = 1
        mock_gp.address = "test_address"
        mock_gp.city = "test_city"
        mock_gp.state = "test_state"
        mock_gp.zip = "test_zip"
        mock_gp.country = "test_country"

        mock_session = MagicMock()
        mock_geocoding_api_address.return_value = None

        process_location_and_outlines(mock_session, mock_gp)
        mock_geocoding_api_address.assert_called_with(
            "test_address",
            "test_city",
            "test_state",
            "test_zip",
            "test_country",
        )
        mock_insert_google_data.assert_called_with(mock_session, mock_gp, -1, -1, [])


if __name__ == "__main__":
    unittest.main()
