"""Module containing service functions outlines only path"""

from app.config import Config
from app.google_api_calls import geocoding_api_coordinate
from app.helper import extract_building_polygons, insert_google_outlines

logger = Config.logger


def process_outlines_only(session, giving_partner):
    """Module that processes outlines only for each GP"""
    logger.info(
        "Processing outline only for giving partner",
        value={
            "giving_partner_id": str(giving_partner.id),
        },
    )
    try:
        geocoding_result = geocoding_api_coordinate(
            giving_partner.latitude, giving_partner.longitude
        )

        destinations = geocoding_result.get("destinations", [])
        building_outlines = extract_building_polygons(destinations)

        if building_outlines:
            insert_google_outlines(
                session,
                giving_partner.id,
                building_outlines,
            )
        else:
            logger.info(
                "Unable to find outlines for giving partner",
                value={
                    "giving_partner_id": str(giving_partner.id),
                },
            )
    except Exception:
        logger.error(
            "Failure in process_outlines_only",
            value={
                "giving_partner_id": str(giving_partner.id),
            },
            exc_info=True,
        )
