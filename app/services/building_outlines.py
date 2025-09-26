"""Module containing service functions outlines only path"""

from app.config import Config
from app.google_api_calls import geocoding_api_address
from app.helper import (
    extract_building_polygons,
    get_giving_partners,
    insert_google_outlines,
)

logger = Config.logger


def run_outlines(session):
    """run_outlines"""
    gp_ids = [int(x.strip()) for x in Config.GP_IDS.split(",") if x.strip()]
    if not gp_ids:
        logger.info(
            "`GP_IDS` is empty",
        )
        return

    result = get_giving_partners(session, gp_ids)
    if len(result) == 0:
        logger.info(
            "No Giving Partner(s) to process",
        )
        return

    for giving_partner in result:
        try:
            process_outlines(session, giving_partner)
        except Exception:
            logger.error(
                "Error processing outlines for giving partner",
                value={
                    "giving_partner_id": str(giving_partner.donee_id),
                },
                exc_info=True,
            )


def process_outlines(session, giving_partner):
    """process_outlines"""
    logger.info(
        "Processing outline for giving partner",
        value={
            "giving_partner_id": str(giving_partner.donee_id),
        },
    )
    try:
        geocoding_result = geocoding_api_address(
            giving_partner.address,
            giving_partner.city,
            giving_partner.state,
            giving_partner.zip,
            giving_partner.country,
        )

        destinations = (geocoding_result or {}).get("destinations", [])
        building_outlines = extract_building_polygons(destinations)

        if building_outlines:
            insert_google_outlines(
                session,
                giving_partner.donee_id,
                building_outlines,
            )
        else:
            logger.info(
                "Unable to find outlines for giving partner",
                value={
                    "giving_partner_id": str(giving_partner.donee_id),
                },
            )
    except Exception:
        logger.error(
            "Failure in process_outlines",
            value={
                "giving_partner_id": str(giving_partner.donee_id),
            },
            exc_info=True,
        )
