"""unitest module for testing"""

import unittest
from argparse import Namespace
from unittest.mock import MagicMock, patch

import helper
import main
from models import GivingPartners
from config import Config


class TestGPProcessor(unittest.TestCase):
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

        with patch("sys.argv", ["main.py", "--id", "123", "--cache_check", "False"]):
            args = main.parse_args()
            self.assertEqual(args.id, 123)
            self.assertTrue(args.cache_check, False)

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
    def test_main(
        self, mock_parse_args, mock_process_gp, mock_get_session, mock_get_engine
    ):
        """unit test to check whether the select query works or not"""
        with patch("main.redis.Redis") as mock_redis:
            mock_redis_server1 = {}
            mock_redis.side_effect = [mock_redis_server1, {"1": "test_gp"}]
            mock_engine = MagicMock()
            mock_get_engine.return_value = mock_engine
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session
            mock_result = MagicMock()
            mock_args = Namespace(enable_autocomplete=True)
            mock_parse_args.return_value = mock_args

            mock_row = MagicMock()
            mock_row.id = "1"
            mock_result.all.return_value = [mock_row]
            mock_session.scalars.return_value = mock_result
            for result in mock_result:
                mock_process_gp.assert_called_with(
                    result,
                    mock_session,
                    mock_redis_server1,
                    mock_args.enable_autocomplete,
                )
            for result in mock_result:
                mock_process_gp.assert_not_called()

    @patch("main.get_session")
    @patch("main.autocomplete_check")
    @patch("helper.geocoding_api")
    @patch("helper.preprocess_building_outlines")
    def test_process_gp_autocomplete_success(
        self,
        mock_preprocess_building_outlines,
        mock_geocoding_api,
        mock_autocomplete,
        mock_get_session,
    ):
        """testing funciton for cases with a passing autocomplete check"""
        with patch("main.redis.Redis") as mock_redis:
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

            mock_geocoding_api.return_value = MagicMock()
            mock_preprocess_building_outlines.return_value = MagicMock()

            # Mock a successful autocomplete check
            mock_redis_server = MagicMock()
            mock_redis.return_value = mock_redis_server
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session
            mock_autocomplete.return_value = "place_id_123"

            main.process_gp(
                mock_gp, mock_session, mock_redis_server, autocomplete_toggle=True
            )
            self.assertEqual(
                mock_session.add.call_args[0][0].address,
                f"{mock_gp.address}, {mock_gp.city}, {mock_gp.state}, {mock_gp.country}",
            )
            mock_session.commit.assert_called_once()
            mock_redis_server.assert_not_called()

    def test_process_gp_text_search_success(self):
        """testing function for cases with failure of autocomplete check and text search api success"""  # pylint: disable=line-too-long
        with patch("main.get_session") as mock_get_session, patch(
            "main.autocomplete_check"
        ) as mock_autocomplete, patch("main.text_search") as mock_text_search, patch(
            "checks.check_topmost"
        ) as mock_check_topmost, patch(
            "helper.geocoding_api"
        ) as mock_geocoding_api, patch(
            "helper.preprocess_building_outlines"
        ) as mock_preprocess_building_outlines, patch(
            "main.redis.Redis"
        ) as mock_redis:
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

            mock_geocoding_api.return_value = MagicMock()
            mock_preprocess_building_outlines.return_value = MagicMock()

            mock_autocomplete.return_value = None
            mock_top_result = {
                "displayName": {"text": "Faith Center"},
                "formattedAddress": "123 test Rd, Hope City, HC, USA",
                "location": {"latitude": 55.66, "longitude": 33.45},
                "id": "api_id_456",
            }
            mock_text_search.return_value = [mock_top_result]

            mock_check_topmost.return_value = True

            mock_session = MagicMock()
            mock_get_session.return_value = mock_session
            mock_redis_server = MagicMock()
            mock_redis.return_value = mock_redis_server
            main.process_gp(mock_gp, mock_session, mock_redis_server)
            mock_text_search.assert_called_with(mock_gp)
            self.assertEqual(
                mock_session.add.call_args[0][0].address,
                mock_top_result["formattedAddress"],
            )
            mock_session.commit.assert_called_once()
            mock_redis_server.assert_not_called()

    @patch("main.get_session")
    @patch("main.autocomplete_check")
    @patch("main.text_search")
    def test_process_gp_no_hits(
        self, mock_text_search, mock_autocomplete, mock_get_session
    ):
        """testing funciton for cases with autcomplete check fail, and no hits for text search api call"""  # pylint: disable=line-too-long
        with patch("main.redis.Redis") as mock_redis:
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
            mock_redis_server = MagicMock()
            mock_redis.return_value = mock_redis_server

            main.process_gp(mock_gp, mock_session, mock_redis_server)
            mock_text_search.assert_called_with(mock_gp)
            mock_session.add.assert_not_called()
            mock_config = Config()
            mock_config.GP_CACHE_EXPIRE = 30
            expiry_in_seconds = mock_config.GP_CACHE_EXPIRE * 86400
            mock_redis_server.setex.assert_called_with(
                mock_gp.id, expiry_in_seconds, mock_gp.name
            )

    def test_process_gp_failure_on_hit(
        self,
    ):
        """testing function for cases of autocomplete check fail, and the topmost hit of text search api not matching gp from donee_info table"""  # pylint: disable=line-too-long
        with patch("main.get_session") as mock_get_session, patch(
            "main.autocomplete_check"
        ) as mock_autocomplete, patch("main.text_search") as mock_text_search, patch(
            "checks.check_topmost"
        ) as mock_check_topmost, patch(
            "helper.geocoding_api"
        ) as mock_geocoding_api, patch(
            "helper.preprocess_building_outlines"
        ) as mock_preprocess_building_outlines, patch(
            "main.redis.Redis"
        ) as mock_redis:
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
            mock_geocoding_api.return_value = MagicMock()
            mock_preprocess_building_outlines.return_value = MagicMock()
            mock_top_result = {
                "displayName": {"text": "Grace banquet center"},
                "formattedAddress": "123 test Rd, test City, TS, USA",
                "location": {"latitude": 45.67, "longitude": 34.67},
                "id": "api_id_456",
            }
            mock_text_search.return_value = [mock_top_result]
            mock_session = MagicMock()
            mock_check_topmost.return_value = False
            mock_get_session.return_value = mock_session
            mock_redis_server = MagicMock()
            mock_redis.return_value = mock_redis_server

            main.process_gp(mock_gp, mock_session, mock_redis_server)
            mock_text_search.assert_called_with(mock_gp)
            mock_session.add.assert_not_called()
            mock_config = Config()
            mock_config.GP_CACHE_EXPIRE = 30
            expiry_in_seconds = mock_config.GP_CACHE_EXPIRE * 86400
            mock_redis_server.setex.assert_called_with(
                mock_gp.id, expiry_in_seconds, mock_gp.name
            )


if __name__ == "__main__":
    unittest.main()
