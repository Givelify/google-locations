"""Module containing service functions for the location and outlines path"""

import json
import os
import uuid

import boto3

from app.config import Config
from app.google_api_calls import geocoding_api_address
from app.helper import (
    extract_building_polygons,
    get_giving_partners,
    get_lat_lon,
    insert_google_data,
)

logger = Config.logger


def run_location_and_outlines(session, sns_client):
    """Main module"""
    result = get_giving_partners(session)
    if len(result) == 0:
        logger.info(
            "No Giving Partner(s) to process",
        )
        return
    for giving_partner in result:
        try:
            process_location_and_outlines(session, giving_partner)
            publish_sns_search_sync(sns_client, giving_partner.donee_id)
        except Exception:
            logger.error(
                "Error processing location and outlines for giving partner",
                value={
                    "giving_partner_id": str(giving_partner.donee_id),
                },
                exc_info=True,
            )


def process_location_and_outlines(session, giving_partner):
    """Module that processes location and outlines each GP"""
    logger.info(
        "Processing location and outline for giving partner",
        value={
            "giving_partner_id": str(giving_partner.donee_id),
        },
    )
    geocoding_result = geocoding_api_address(
        giving_partner.address,
        giving_partner.city,
        giving_partner.state,
        giving_partner.zip,
        giving_partner.country,
    )
    destinations = (geocoding_result or {}).get("destinations", [])
    building_outlines = extract_building_polygons(destinations)
    latitude, longitude = get_lat_lon(destinations)

    insert_google_data(
        session,
        giving_partner,
        latitude,
        longitude,
        building_outlines,
    )


def get_sns_client():
    """Return sns client for donee_geocoder"""
    kwargs = {}

    # Set endpoint if running against LocalStack
    localstack_endpoint = os.environ.get("LOCALSTACK_HOSTNAME")
    if localstack_endpoint:
        kwargs["endpoint_url"] = localstack_endpoint

        # LocalStack still requires dummy credentials
        kwargs["aws_access_key_id"] = os.environ.get("AWS_ACCESS_KEY")
        kwargs["aws_secret_access_key"] = os.environ.get("AWS_SECRET_KEY")
        kwargs["region_name"] = os.environ.get("AWS_REGION")

    return boto3.client("sns", **kwargs)


def publish_sns_search_sync(sns_client, giving_partner_id: int) -> None:
    """
    Publish a message to the SNS topic to sync the gp to search.
    """
    sns_message = {
        "data": {"giving_partner_id": giving_partner_id, "operation": "update"}
    }

    sns_client.publish(
        TopicArn=Config.AWS_SNS_TOPIC,
        Message=json.dumps(sns_message),
        MessageGroupId="group",
        MessageDeduplicationId=str(uuid.uuid4()),
        MessageAttributes={
            "eventKey": {
                "DataType": "String",
                "StringValue": "search.giving-partner-search-sync-requested",
            }
        },
    )

    logger.info(
        "Published SNS message for giving_partner",
        value={
            "giving_partner_id": str(giving_partner_id),
        },
    )
