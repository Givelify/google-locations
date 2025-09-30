"""unitest module for testing"""

import json
import unittest
import uuid
from unittest.mock import MagicMock, call, patch

from app.config import Config
from app.scripts.donee_geocoder import main
from app.services.location_and_outlines import (
    get_sns_client,
    process_location_and_outlines,
    publish_sns_search_sync,
    run_location_and_outlines,
)


class TestDoneeGeocoder(unittest.TestCase):
    """testing class for donee_geocoder.py"""

    def setUp(self):
        """Setup mocks before each test"""
        self.mock_engine = MagicMock()
        self.mock_session = MagicMock()
        self.mock_sns = MagicMock()
        self.mock_client = MagicMock()

        self.mock_gp_1 = MagicMock()
        self.mock_gp_1.donee_id = 1
        self.mock_gp_1.address = "test_address"
        self.mock_gp_1.city = "test_city"
        self.mock_gp_1.state = "test_state"
        self.mock_gp_1.zip = "test_zip"
        self.mock_gp_1.country = "test_country"

        self.mock_gp_2 = MagicMock()
        self.mock_gp_2.donee_id = 2
        self.mock_gp_2.address = "test_address_2"
        self.mock_gp_2.city = "test_city_2"
        self.mock_gp_2.state = "test_state_2"
        self.mock_gp_2.zip = "test_zip_2"
        self.mock_gp_2.country = "test_country_2"

    @patch("app.scripts.donee_geocoder.get_sns_client")
    @patch("app.scripts.donee_geocoder.get_engine")
    @patch("app.scripts.donee_geocoder.get_session")
    @patch("app.scripts.donee_geocoder.run_location_and_outlines")
    def test_main_donee_geocoder(
        self,
        mock_run_location_and_outlines,
        mock_get_session,
        mock_get_engine,
        mock_get_sns_client,
    ):
        """Test main() donee_geocoder flow"""
        mock_get_engine.return_value = self.mock_engine
        mock_get_sns_client.return_value = self.mock_sns
        mock_get_session.return_value.__enter__.return_value = self.mock_session

        main()

        mock_run_location_and_outlines.assert_called_with(
            self.mock_session, self.mock_sns
        )

    @patch("app.services.location_and_outlines.publish_sns_search_sync")
    @patch("app.services.location_and_outlines.process_location_and_outlines")
    @patch("app.services.location_and_outlines.get_giving_partners")
    def test_run_location_and_outlines(
        self,
        mock_get_giving_partners,
        mock_process_location_and_outlines,
        mock_publish_sns_search_sync,
    ):
        """Test run_location_and_outlines() success flow"""
        mock_get_giving_partners.return_value = [self.mock_gp_1, self.mock_gp_2]

        run_location_and_outlines(self.mock_session, self.mock_sns)
        mock_get_giving_partners.assert_called_with(self.mock_session)
        mock_process_location_and_outlines.assert_has_calls(
            [
                call(self.mock_session, self.mock_gp_1),
                call(self.mock_session, self.mock_gp_2),
            ]
        )
        mock_publish_sns_search_sync.assert_has_calls(
            [
                call(self.mock_sns, self.mock_gp_1.donee_id),
                call(self.mock_sns, self.mock_gp_2.donee_id),
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
        mock_get_giving_partners.return_value = []

        run_location_and_outlines(self.mock_session, self.mock_sns)
        mock_get_giving_partners.assert_called_with(self.mock_session)
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
        mock_session = MagicMock()
        mock_geocoding_results = {"destinations": [{MagicMock()}]}
        mock_geocoding_api_address.return_value = mock_geocoding_results
        mock_building_outlines = [{MagicMock()}]
        mock_extract_building_polygons.return_value = mock_building_outlines
        mock_get_lat_lon.return_value = (10, 10)

        process_location_and_outlines(mock_session, self.mock_gp_1)
        mock_geocoding_api_address.assert_called_with(
            "test_address",
            "test_city",
            "test_state",
            "test_zip",
            "test_country",
        )
        mock_insert_google_data.assert_called_with(
            mock_session, self.mock_gp_1, 10, 10, mock_building_outlines
        )

    @patch("app.services.location_and_outlines.geocoding_api_address")
    @patch("app.services.location_and_outlines.insert_google_data")
    def test_process_location_and_outlines_no_results(
        self,
        mock_insert_google_data,
        mock_geocoding_api_address,
    ):
        """process_location_and_outlines where no results"""
        mock_geocoding_api_address.return_value = None

        process_location_and_outlines(self.mock_session, self.mock_gp_1)
        mock_geocoding_api_address.assert_called_with(
            "test_address",
            "test_city",
            "test_state",
            "test_zip",
            "test_country",
        )
        mock_insert_google_data.assert_called_with(
            self.mock_session, self.mock_gp_1, -1, -1, []
        )

    @patch.object(Config, "AWS_SNS_TOPIC", "test_sns_topic")
    @patch("app.services.location_and_outlines.uuid.uuid4")
    def test_publish_sns_search_sync(
        self,
        mock_uuid,
    ):
        """Test that SNS message is published correctly"""
        mock_uuid.return_value = uuid.UUID("12345678-1234-5678-1234-567812345678")
        giving_partner_id = 42

        publish_sns_search_sync(self.mock_sns, giving_partner_id)

        expected_message = {
            "data": {"giving_partner_id": giving_partner_id, "operation": "update"}
        }

        self.mock_sns.publish.assert_called_once_with(
            TopicArn="test_sns_topic",
            Message=json.dumps(expected_message),
            MessageGroupId="group",
            MessageDeduplicationId=str(mock_uuid.return_value),
            MessageAttributes={
                "eventKey": {
                    "DataType": "String",
                    "StringValue": "search.giving-partner-search-sync-requested",
                }
            },
        )

    @patch("app.services.location_and_outlines.boto3.client")
    @patch.dict("app.services.location_and_outlines.os.environ", {}, clear=True)
    def test_get_sns_client_without_localstack(
        self,
        mock_boto_client,
    ):
        """Test get_sns_client with no LocalStack env vars"""
        mock_boto_client.return_value = self.mock_client

        client = get_sns_client()

        mock_boto_client.assert_called_once_with("sns")
        self.assertEqual(client, self.mock_client)

    @patch("app.services.location_and_outlines.boto3.client")
    @patch.dict(
        "app.services.location_and_outlines.os.environ",
        {
            "LOCALSTACK_HOSTNAME": "http://localhost:4566",
            "AWS_ACCESS_KEY": "test",
            "AWS_SECRET_KEY": "secret",
            "AWS_REGION": "us-east-1",
        },
        clear=True,
    )
    def test_get_sns_client_with_localstack(
        self,
        mock_boto_client,
    ):
        """Test get_sns_client with LocalStack env vars"""
        mock_boto_client.return_value = self.mock_client

        client = get_sns_client()

        # Assert boto3 client called with correct kwargs
        mock_boto_client.assert_called_once_with(
            "sns",
            endpoint_url="http://localhost:4566",
            aws_access_key_id="test",
            aws_secret_access_key="secret",
            region_name="us-east-1",
        )
        self.assertEqual(client, self.mock_client)


if __name__ == "__main__":
    unittest.main()
