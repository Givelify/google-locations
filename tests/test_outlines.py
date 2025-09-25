"""unitest module for testing"""

import unittest
from unittest.mock import MagicMock, call, patch

from app.scripts.outlines import main
from app.services.building_outlines import process_outlines, run_outlines


class TestOutlines(unittest.TestCase):
    """testing class for outlines.py"""

    @patch("app.scripts.outlines.get_engine")
    @patch("app.scripts.outlines.get_session")
    @patch("app.scripts.outlines.run_outlines")
    def test_main_outlines(
        self,
        mock_run_outlines,
        mock_get_session,
        mock_get_engine,
    ):
        """Test main() outlines flow"""
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine

        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        main()

        mock_run_outlines.assert_called_with(mock_session)

    @patch("app.services.building_outlines.Config.GP_IDS", "1,2,3,4")
    @patch("app.services.building_outlines.process_outlines")
    @patch("app.services.building_outlines.get_giving_partners")
    def test_run_outlines(
        self,
        mock_get_giving_partners,
        mock_process_outlines_only,
    ):
        """Test run_outlines() success flow"""
        mock_session = MagicMock()

        mock_gp_1 = MagicMock()
        mock_gp_1.id = 1
        mock_gp_2 = MagicMock()
        mock_gp_2.id = 2
        mock_get_giving_partners.return_value = [mock_gp_1, mock_gp_2]

        run_outlines(mock_session)
        mock_get_giving_partners.assert_called_with(mock_session, [1, 2, 3, 4])
        mock_process_outlines_only.assert_has_calls(
            [
                call(mock_session, mock_gp_1),
                call(mock_session, mock_gp_2),
            ]
        )

    @patch("app.services.building_outlines.geocoding_api_address")
    @patch("app.services.building_outlines.extract_building_polygons")
    @patch("app.services.building_outlines.insert_google_outlines")
    def test_process_outlines_no_outlines(
        self,
        mock_insert_google_outlines,
        mock_extract_building_polygons,
        mock_geocoding_api_address,
    ):
        """Testing process_outlines no outlines"""
        mock_gp = MagicMock()

        mock_session = MagicMock()
        mock_geocoding_results = {"destinations": [{MagicMock()}]}
        mock_geocoding_api_address.return_value = mock_geocoding_results
        mock_building_outlines = []
        mock_extract_building_polygons.return_value = mock_building_outlines

        process_outlines(mock_session, mock_gp)

        mock_insert_google_outlines.assert_not_called()

    @patch("app.services.building_outlines.geocoding_api_address")
    @patch("app.services.building_outlines.extract_building_polygons")
    @patch("app.services.building_outlines.insert_google_outlines")
    def test_process_outlines_success(
        self,
        mock_insert_google_outlines,
        mock_extract_building_polygons,
        mock_geocoding_api_address,
    ):
        """Testing process_outlines success"""
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

        process_outlines(mock_session, mock_gp)

        mock_geocoding_api_address.assert_called_with(
            "test_address",
            "test_city",
            "test_state",
            "test_zip",
            "test_country",
        )
        mock_insert_google_outlines.assert_called_with(
            mock_session,
            mock_gp.donee_id,
            mock_building_outlines,
        )
