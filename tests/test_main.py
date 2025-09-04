"""unitest module for testing"""

import unittest
from unittest.mock import MagicMock, call, patch

from app.enums import FilterType
from app.main import main, run_location_and_outlines, run_outlines_only
from app.services.building_outlines_only import process_outlines_only
from app.services.location_and_outlines import process_location_and_outlines


class TestMain(unittest.TestCase):
    """testing class for main.py"""

    @patch("app.main.Config.BUILDING_OUTLINES_ONLY", True)
    @patch("app.main.get_engine")
    @patch("app.main.get_session")
    @patch("app.main.run_outlines_only")
    @patch("app.main.run_location_and_outlines")
    def test_main_outlines_only(
        self,
        mock_run_location_and_outlines,
        mock_run_outlines_only,
        mock_get_session,
        mock_get_engine,
    ):
        """Test main() outlines only flow"""
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine

        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        main()

        mock_run_outlines_only.assert_called_with(mock_session)
        mock_run_location_and_outlines.assert_not_called()

    @patch("app.main.Config.BUILDING_OUTLINES_ONLY", False)
    @patch("app.main.get_engine")
    @patch("app.main.get_session")
    @patch("app.main.run_outlines_only")
    @patch("app.main.run_location_and_outlines")
    def test_main_location_and_outlines(
        self,
        mock_run_location_and_outlines,
        mock_run_outlines_only,
        mock_get_session,
        mock_get_engine,
    ):
        """Test main() location and outlines flow"""
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine

        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        main()

        mock_run_outlines_only.assert_not_called()
        mock_run_location_and_outlines.assert_called_with(mock_session)

    @patch("app.main.process_location_and_outlines")
    @patch("app.main.get_giving_partners")
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
        mock_get_giving_partners.assert_called_with(
            mock_session, FilterType.LOCATION_AND_OUTLINES
        )
        mock_process_location_and_outlines.assert_has_calls(
            [
                call(mock_session, mock_gp_1),
                call(mock_session, mock_gp_2),
            ]
        )

    @patch("app.main.process_outlines_only")
    @patch("app.main.get_giving_partners")
    def test_run_outlines_only(
        self,
        mock_get_giving_partners,
        mock_process_outlines_only,
    ):
        """Test run_outlines_only() success flow"""
        mock_session = MagicMock()

        mock_gp_1 = MagicMock()
        mock_gp_1.id = 1
        mock_gp_2 = MagicMock()
        mock_gp_2.id = 2
        mock_get_giving_partners.return_value = [mock_gp_1, mock_gp_2]

        run_outlines_only(mock_session)
        mock_get_giving_partners.assert_called_with(
            mock_session, FilterType.OUTLINES_ONLY
        )
        mock_process_outlines_only.assert_has_calls(
            [
                call(mock_session, mock_gp_1),
                call(mock_session, mock_gp_2),
            ]
        )

    @patch("app.services.location_and_outlines.Config.ENABLE_AUTOCOMPLETE", True)
    @patch("app.services.location_and_outlines.autocomplete_check")
    @patch("app.services.location_and_outlines.process_autocomplete_results")
    def test_process_location_and_outlines_autocomplete(
        self,
        mock_process_autocomplete_results,
        mock_autocomplete_check,
    ):
        """process_location_and_outlines autocomplete"""
        mock_gp = MagicMock()
        mock_gp.id = 1

        mock_session = MagicMock()
        mock_autocomplete_check.return_value = "place_id_123"
        mock_process_autocomplete_results.return_value = True

        process_location_and_outlines(mock_session, mock_gp)
        mock_autocomplete_check.assert_called_with(mock_gp)
        mock_process_autocomplete_results.assert_called_with(
            mock_session, mock_gp, "place_id_123"
        )

    @patch("app.services.location_and_outlines.Config.ENABLE_AUTOCOMPLETE", True)
    @patch("app.services.location_and_outlines.autocomplete_check")
    @patch("app.services.location_and_outlines.process_autocomplete_results")
    @patch("app.services.location_and_outlines.text_search")
    @patch("app.services.location_and_outlines.text_search_similarity_check")
    @patch("app.services.location_and_outlines.process_text_search_results")
    def test_process_location_and_outlines_autocomplete_no_results_backup(
        self,
        mock_process_text_search_results,
        mock_text_search_similarity_check,
        mock_text_search,
        mock_process_autocomplete_results,
        mock_autocomplete_check,
    ):
        """process_location_and_outlines autocomplete text search backup is used"""
        mock_gp = MagicMock()
        mock_gp.id = 1

        mock_session = MagicMock()
        mock_autocomplete_check.return_value = None
        mock_top_result = {
            "displayName": {"text": "Faith Center"},
            "formattedAddress": "123 test Rd, Hope City, HC, USA",
            "location": {"latitude": 55.66, "longitude": 33.45},
            "id": "api_id_456",
        }
        mock_text_search.return_value = [mock_top_result]
        mock_text_search_similarity_check.return_value = True
        mock_process_text_search_results.return_value = None

        process_location_and_outlines(mock_session, mock_gp)
        mock_autocomplete_check.assert_called_with(mock_gp)
        mock_process_autocomplete_results.assert_not_called()
        mock_text_search.assert_called_with(mock_gp)
        mock_text_search_similarity_check.assert_called_with(mock_gp, mock_top_result)
        mock_process_text_search_results.assert_called_with(
            mock_session, mock_gp, mock_top_result
        )

    @patch("app.services.location_and_outlines.Config.ENABLE_AUTOCOMPLETE", False)
    @patch("app.services.location_and_outlines.autocomplete_check")
    @patch("app.services.location_and_outlines.process_autocomplete_results")
    @patch("app.services.location_and_outlines.text_search")
    @patch("app.services.location_and_outlines.text_search_similarity_check")
    @patch("app.services.location_and_outlines.process_text_search_results")
    def test_process_location_and_outlines_text_search_success(
        self,
        mock_process_text_search_results,
        mock_text_search_similarity_check,
        mock_text_search,
        mock_process_autocomplete_results,
        mock_autocomplete_check,
    ):
        """Testing process_location_and_outlines not autocomplete, using text search"""
        mock_gp = MagicMock()
        mock_gp.id = 1

        mock_top_result = {
            "displayName": {"text": "Faith Center"},
            "formattedAddress": "123 test Rd, Hope City, HC, USA",
            "location": {"latitude": 55.66, "longitude": 33.45},
            "id": "api_id_456",
        }
        mock_text_search.return_value = [mock_top_result]
        mock_text_search_similarity_check.return_value = True
        mock_process_text_search_results.return_value = None
        mock_session = MagicMock()

        process_location_and_outlines(mock_session, mock_gp)

        mock_autocomplete_check.assert_not_called()
        mock_process_autocomplete_results.assert_not_called()

        mock_text_search.assert_called_with(mock_gp)
        mock_text_search_similarity_check.assert_called_with(mock_gp, mock_top_result)
        mock_process_text_search_results.assert_called_with(
            mock_session, mock_gp, mock_top_result
        )

    @patch("app.services.location_and_outlines.Config.ENABLE_AUTOCOMPLETE", True)
    @patch("app.services.location_and_outlines.autocomplete_check")
    @patch("app.services.location_and_outlines.process_autocomplete_results")
    @patch("app.services.location_and_outlines.text_search")
    @patch("app.services.location_and_outlines.text_search_similarity_check")
    @patch("app.services.location_and_outlines.process_text_search_results")
    def test_process_location_and_outlines_no_hits(
        self,
        mock_process_text_search_results,
        mock_text_search_similarity_check,
        mock_text_search,
        mock_process_autocomplete_results,
        mock_autocomplete_check,
    ):
        """process_location_and_outlines where autocomplete and text search no hits"""
        mock_gp = MagicMock()
        mock_gp.id = 1

        mock_session = MagicMock()

        mock_autocomplete_check.return_value = None
        mock_text_search.return_value = []
        mock_session = MagicMock()

        process_location_and_outlines(mock_session, mock_gp)

        mock_autocomplete_check.assert_called_with(mock_gp)
        mock_process_autocomplete_results.assert_not_called()
        mock_text_search.assert_called_with(mock_gp)
        mock_text_search_similarity_check.assert_not_called()
        mock_process_text_search_results.assert_not_called()

    @patch("app.services.building_outlines_only.geocoding_api_coordinate")
    @patch("app.services.building_outlines_only.extract_building_polygons")
    @patch("app.services.building_outlines_only.insert_google_outlines")
    def test_process_outlines_only_success(
        self,
        mock_insert_google_outlines,
        mock_extract_building_polygons,
        mock_geocoding_api_coordinate,
    ):
        """Testing process_outlines_only success"""
        mock_gp = MagicMock()
        mock_gp.id = 1
        mock_gp.latitude = "123"
        mock_gp.longitude = "321"

        mock_session = MagicMock()
        mock_geocoding_results = {"destinations": [{MagicMock()}]}
        mock_geocoding_api_coordinate.return_value = mock_geocoding_results
        mock_building_outlines = [{MagicMock()}]
        mock_extract_building_polygons.return_value = mock_building_outlines

        process_outlines_only(mock_session, mock_gp)

        mock_geocoding_api_coordinate.assert_called_with("123", "321")
        mock_insert_google_outlines.assert_called_with(
            mock_session,
            mock_gp.id,
            mock_building_outlines,
        )

    @patch("app.services.building_outlines_only.geocoding_api_coordinate")
    @patch("app.services.building_outlines_only.extract_building_polygons")
    @patch("app.services.building_outlines_only.insert_google_outlines")
    def test_process_outlines_only_no_outlines(
        self,
        mock_insert_google_outlines,
        mock_extract_building_polygons,
        mock_geocoding_api_coordinate,
    ):
        """Testing process_outlines_only no outlines"""
        mock_gp = MagicMock()
        mock_gp.id = 1
        mock_gp.latitude = "123"
        mock_gp.longitude = "321"

        mock_session = MagicMock()
        mock_geocoding_results = {"destinations": [{MagicMock()}]}
        mock_geocoding_api_coordinate.return_value = mock_geocoding_results
        mock_building_outlines = []
        mock_extract_building_polygons.return_value = mock_building_outlines

        process_outlines_only(mock_session, mock_gp)

        mock_insert_google_outlines.assert_not_called()


if __name__ == "__main__":
    unittest.main()
