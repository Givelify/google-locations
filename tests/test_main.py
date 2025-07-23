"""unitest module for testing"""

import unittest
from unittest.mock import MagicMock, call, patch

import helper
import main


class TestMain(unittest.TestCase):
    """testing class for main.py"""

    def test_preprocess_building_outlines(self):
        """tests for successfully preprocessing building outlines returned by geocoding API"""
        building_outlines = [
            {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-92.42324, 36.23432423],
                        [-92.32432, 36.23423],
                        [-92.235235, 36.235235],
                        [-92.325552, 36.2343243],
                        [-92.25245245, 36.425245245],
                    ]
                ],
            },
            None,
            {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [-92.324234, 36.34141],
                            [-92.325235, 36.325235],
                            [-92.2352353, 36.235235],
                            [-92.235235, 36.2352353],
                            [-92.23523523, 36.3252353],
                        ]
                    ],
                    [
                        [
                            [-346534634, 45245245],
                            [-42524524, 2525223452],
                            [-25234532523, 2454254254],
                            [-245234523532, 5235325],
                            [-235235325, 2352353254],
                        ]
                    ],
                ],
            },
            {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [-92.13413414, 36.13414],
                        [-92.3124314, 36.23532],
                        [-92.5352, 36.245245],
                        [-92.25245, 36.245245],
                        [-92.245245, 36.5245245],
                    ],
                    [
                        [-5245245, 52452],
                        [-52352, 253252],
                        [-235235, 2534525],
                        [-23525, 5235323523525],
                        [-2352, 252352],
                    ],
                ],
            },
        ]

        preprocessed_outlines = helper.preprocess_building_outlines(
            building_outlines[0]
        )
        self.assertEqual(preprocessed_outlines[:7], "POLYGON")
        preprocessed_outlines = helper.preprocess_building_outlines(
            building_outlines[1]
        )
        self.assertIsNone(preprocessed_outlines)
        preprocessed_outlines = helper.preprocess_building_outlines(
            building_outlines[2]
        )
        self.assertEqual(preprocessed_outlines[:12], "MULTIPOLYGON")
        with self.assertRaises(Exception):
            helper.preprocess_building_outlines(building_outlines[3])

    def test_parse_args(self):
        """tests for parsing command line arguments"""
        with patch("sys.argv", ["main.py", "--enable_autocomplete"]):
            args = main.parse_args()
            self.assertTrue(args.enable_autocomplete)
            self.assertIsNone(args.id)

        with patch("sys.argv", ["main.py", "--id", "123", "--enable_autocomplete"]):
            args = main.parse_args()
            self.assertEqual(args.id, 123)
            self.assertTrue(args.enable_autocomplete)

        with patch("sys.argv", ["main.py"]):
            args = main.parse_args()
            self.assertFalse(args.enable_autocomplete)

        with patch("sys.argv", ["main.py", "--id", "string"]):
            with self.assertRaises(SystemExit):
                helper.parse_args()
        with patch("sys.argv", ["main.py", "--id", "string1", "string2"]):
            with self.assertRaises(SystemExit):
                helper.parse_args()
        with patch("sys.argv", ["main.py", "--id", "500", "string2"]):
            with self.assertRaises(SystemExit):
                helper.parse_args()
        with patch("sys.argv", ["main.py", "xyz"]):
            with self.assertRaises(SystemExit):
                helper.parse_args()

    @patch("main.get_engine")
    @patch("main.get_session")
    @patch("main.process_gp")
    @patch("main.parse_args")
    @patch("main.get_giving_partners")
    def test_main(
        self,
        mock_get_giving_partners,
        mock_parse_args,
        mock_process_gp,
        mock_get_session,
        mock_get_engine,
    ):
        """Test main() success flow"""
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_args = MagicMock()
        mock_args.id = None
        mock_args.enable_autocomplete = True
        mock_parse_args.return_value = mock_args

        mock_gp_1 = MagicMock()
        mock_gp_1.id = 1
        mock_gp_2 = MagicMock()
        mock_gp_2.id = 2
        mock_get_giving_partners.return_value = [mock_gp_1, mock_gp_2]

        main.main()
        mock_get_giving_partners.assert_called_with(mock_session, None)
        mock_process_gp.assert_has_calls(
            [
                call(mock_gp_1, mock_session, True),
                call(mock_gp_2, mock_session, True),
            ]
        )

    @patch("main.autocomplete_check")
    @patch("main.process_autocomplete_results")
    def test_process_gp_autocomplete_success(
        self,
        mock_process_autocomplete_results,
        mock_autocomplete_check,
    ):
        """Testing process_gp using autocomplete"""
        mock_gp = MagicMock()
        mock_gp.id = 1

        mock_session = MagicMock()
        mock_autocomplete_check.return_value = "place_id_123"
        mock_process_autocomplete_results.return_value = True

        main.process_gp(mock_gp, mock_session, enable_autocomplete=True)
        mock_autocomplete_check.assert_called_with(mock_gp)
        mock_process_autocomplete_results.assert_called_with(
            mock_session, mock_gp, "place_id_123"
        )

    @patch("main.autocomplete_check")
    @patch("main.process_autocomplete_results")
    @patch("main.text_search")
    @patch("main.check_topmost")
    @patch("main.process_text_search_results")
    def test_process_gp_autocomplete_no_results_backup(
        self,
        mock_process_text_search_results,
        mock_check_topmost,
        mock_text_search,
        mock_process_autocomplete_results,
        mock_autocomplete_check,
    ):
        """Testing process_gp using autocomplete where text search backup is used"""
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
        mock_check_topmost.return_value = True
        mock_process_text_search_results.return_value = None

        main.process_gp(mock_gp, mock_session, enable_autocomplete=True)
        mock_autocomplete_check.assert_called_with(mock_gp)
        mock_process_autocomplete_results.assert_not_called()
        mock_text_search.assert_called_with(mock_gp)
        mock_check_topmost.assert_called_with(mock_gp, mock_top_result)
        mock_process_text_search_results.assert_called_with(
            mock_session, mock_gp, mock_top_result
        )

    @patch("main.autocomplete_check")
    @patch("main.process_autocomplete_results")
    @patch("main.text_search")
    @patch("main.check_topmost")
    @patch("main.process_text_search_results")
    def test_process_gp_text_search_success(
        self,
        mock_process_text_search_results,
        mock_check_topmost,
        mock_text_search,
        mock_process_autocomplete_results,
        mock_autocomplete_check,
    ):
        """Testing process_gp not using autocomplete, using text search"""
        mock_gp = MagicMock()
        mock_gp.id = 1

        mock_top_result = {
            "displayName": {"text": "Faith Center"},
            "formattedAddress": "123 test Rd, Hope City, HC, USA",
            "location": {"latitude": 55.66, "longitude": 33.45},
            "id": "api_id_456",
        }
        mock_text_search.return_value = [mock_top_result]
        mock_check_topmost.return_value = True
        mock_process_text_search_results.return_value = None
        mock_session = MagicMock()

        main.process_gp(mock_gp, mock_session)

        mock_autocomplete_check.assert_not_called()
        mock_process_autocomplete_results.assert_not_called()

        mock_text_search.assert_called_with(mock_gp)
        mock_check_topmost.assert_called_with(mock_gp, mock_top_result)
        mock_process_text_search_results.assert_called_with(
            mock_session, mock_gp, mock_top_result
        )

    @patch("main.autocomplete_check")
    @patch("main.process_autocomplete_results")
    @patch("main.text_search")
    @patch("main.check_topmost")
    @patch("main.process_text_search_results")
    def test_process_gp_no_hits(
        self,
        mock_process_text_search_results,
        mock_check_topmost,
        mock_text_search,
        mock_process_autocomplete_results,
        mock_autocomplete_check,
    ):
        """Testing process_gp for cases where autocomplete and text search no hits"""
        mock_gp = MagicMock()
        mock_gp.id = 1

        mock_session = MagicMock()

        mock_autocomplete_check.return_value = None
        mock_text_search.return_value = []
        mock_session = MagicMock()

        main.process_gp(mock_gp, mock_session, enable_autocomplete=True)

        mock_autocomplete_check.assert_called_with(mock_gp)
        mock_process_autocomplete_results.assert_not_called()
        mock_text_search.assert_called_with(mock_gp)
        mock_check_topmost.assert_not_called()
        mock_process_text_search_results.assert_not_called()


if __name__ == "__main__":
    unittest.main()
