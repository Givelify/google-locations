"""module for unit testing"""

import unittest
from unittest.mock import MagicMock, patch

from app.config import Config
from app.helper import insert_google_data


class TestHelper(unittest.TestCase):
    """unit test class to test helper"""

    def setUp(self):
        """Setup mocks before each test"""
        self.mock_outlines = MagicMock()
        self.mock_session = MagicMock()

        self.donee_lat = 10
        self.donee_lon = 11
        self.gp_id = 1

        self.mock_gp = MagicMock()
        self.mock_gp.donee_id = self.gp_id

    @patch.object(Config, "DONEE_GEOCODER_ENABLE_OUTLINES", False)
    @patch("app.helper.GivingPartnerOutlines")
    def test_insert_google_data_outlines_disabled(self, mock_gp_outlines):
        """Test insert_google_data outlines disabled"""

        insert_google_data(
            self.mock_session,
            self.mock_gp,
            self.donee_lat,
            self.donee_lon,
            self.mock_outlines,
        )
        mock_gp_outlines.assert_not_called()
        self.mock_session.commit.assert_called()

    @patch.object(Config, "DONEE_GEOCODER_ENABLE_OUTLINES", True)
    @patch("app.helper.GivingPartnerOutlines")
    def test_insert_google_data_outlines_enabled(self, mock_gp_outlines):
        """Test insert_google_data outlines enabled"""

        insert_google_data(
            self.mock_session,
            self.mock_gp,
            self.donee_lat,
            self.donee_lon,
            self.mock_outlines,
        )
        mock_gp_outlines.assert_called_with(
            giving_partner_id=self.mock_gp.donee_id, outlines=self.mock_outlines
        )
        self.mock_session.commit.assert_called()
