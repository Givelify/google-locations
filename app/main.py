"""Module that connects to mysql server and performs database operations"""

import sys

from app.config import Config
from app.enums import FilterType
from app.helper import get_giving_partners
from app.models import get_engine, get_session
from app.services.building_outlines_only import process_outlines_only
from app.services.location_and_outlines import process_location_and_outlines

logger = Config.logger


def main():
    """Main module"""
    engine = None
    try:
        logger.info(f"Database Name {Config.PLATFORM_DB_DATABASE})")
        logger.info(f"Database Host {Config.PLATFORM_DB_HOST_WRITE})")
        logger.info(f"Database Username {Config.PLATFORM_DB_USERNAME})")
        engine = get_engine(
            db_host=Config.PLATFORM_DB_HOST_WRITE,
            db_port=Config.PLATFORM_DB_PORT,
            db_user=Config.PLATFORM_DB_USERNAME,
            db_password=Config.PLATFORM_DB_PASSWORD,
            db_name=Config.PLATFORM_DB_DATABASE,
        )

        with get_session(engine) as session:
            if Config.BUILDING_OUTLINES_ONLY:
                # uses company data for location to find the outline
                run_outlines_only(session)
            else:
                # retrieves google location and uses that to find the outline
                run_location_and_outlines(session)

    except Exception:
        logger.error("Failed to update with Google data.", exc_info=True)
        return 1
    finally:
        if engine:
            engine.dispose()
    return 0


def run_location_and_outlines(session):
    """Main module"""
    result = get_giving_partners(session, FilterType.LOCATION_AND_OUTLINES)
    if len(result) == 0:
        logger.info(
            "No Giving Partner(s) to process",
        )
        return
    for giving_partner in result:
        try:
            process_location_and_outlines(session, giving_partner)
        except Exception:
            logger.error(
                "Error processing location and outlines for giving partner",
                value={
                    "giving_partner_id": str(giving_partner.id),
                },
                exc_info=True,
            )


def run_outlines_only(session):
    """Main module"""
    result = get_giving_partners(session, FilterType.OUTLINES_ONLY)
    if len(result) == 0:
        logger.info(
            "No Giving Partner(s) to process",
        )
        return
    for giving_partner in result:
        try:
            process_outlines_only(session, giving_partner)
        except Exception:
            logger.error(
                "Error processing outlines only for giving partner",
                value={
                    "giving_partner_id": str(giving_partner.id),
                },
                exc_info=True,
            )


if "__main__" == __name__:
    sys.exit(main())
