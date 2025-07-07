"""Module that connects to mysql server and performs database operations"""

import argparse

from sqlalchemy import and_, func, select
from sqlalchemy.exc import SQLAlchemyError

from checks import autocomplete_check, check_topmost
from config import Config
from google_api_calls import text_search
from models import GivingPartnerLocations as gpl
from models import GivingPartners as gp
from models import get_engine, get_session

logger = Config.logger


def base_filter(giving_partner, active, unregistered):
    "base filter to reuse in SELECT queries to retrieve GPs from donee_info DB"
    return [
        giving_partner.active == active,
        giving_partner.unregistered == unregistered,
        giving_partner.country.isnot(None),
        func.trim(giving_partner.country) != "",
    ]


def parse_args():
    """function to parse optional giving partner id command line argument"""
    parser = argparse.ArgumentParser(
        description="optional giving partner id and enable autocomplete check toggle"
    )
    parser.add_argument("--id", type=int)

    parser.add_argument(
        "--enable_autocomplete",
        action="store_true",
        help="Enable autocomplete check",
        default=False,
    )
    try:
        args = parser.parse_args()
    except SystemExit:
        logger.error("parsing --id argument failed: please make sure it is an integer")
        raise
    return args


def main():
    """Main module"""
    try:
        args = parse_args()

        engine = get_engine(
            db_host=Config.DB_HOST,
            db_port=Config.DB_PORT,
            db_user=Config.DB_USER,
            db_password=Config.DB_PASSWORD,
            db_name=Config.DB_NAME,
        )
        # log success
    except SystemExit:
        logger.error("parsing args failed")
        raise
    except SQLAlchemyError as e:
        logger.error(f"Failed to initialize database engine: {e}")  # error log this
        raise
    active = 1
    unregistered = 0

    if args.id is None:
        query = (
            select(gp)
            .join(gpl, gp.id == gpl.giving_partner_id, isouter=True)
            .where(
                and_(
                    gpl.giving_partner_id.is_(None),
                    *base_filter(gp, active, unregistered),
                )
            )
            .limit(1)
        )
    else:
        query = select(gp).where(
            and_(
                gp.id == args.id,
                *base_filter(gp, active, unregistered),
            )
        )
    try:
        with get_session(engine) as session:
            # log the success of creating the session
            result = session.scalars(query).all()
            if len(result) == 0:
                if args.id is None:
                    logger.info("No Giving partners left to process")
                    return
                logger.info(
                    f"No row exists with provided id: {args.id} in the donee_info / giving patners table"  # log this # pylint: disable=line-too-long
                )
                return
            for giving_partner in result:
                logger.info(
                    f"Processing donee_id: {giving_partner.id}, name: {giving_partner.name}, address: {giving_partner.address}, {giving_partner.city}, {giving_partner.state}, {giving_partner.country}"  # pylint: disable=line-too-long
                )
                try:
                    process_gp(
                        giving_partner,
                        session,
                        autocomplete_toggle=args.enable_autocomplete,
                    )
                except (KeyError, TypeError) as e:
                    logger.error(f"Error in process_gp(): {e}")
    except SQLAlchemyError as e:
        logger.error(f"failed to create session: {e}")
    finally:
        engine.dispose()


def process_gp(giving_partner, session, autocomplete_toggle=False):
    """Module that processes each GP"""
    if autocomplete_toggle:
        autocomplete_result = autocomplete_check(giving_partner)
        if autocomplete_result:
            gp_address = f"{giving_partner.address}, {giving_partner.city}, {giving_partner.state}, {giving_partner.country}"  # pylint: disable=line-too-long
            gp_info = gpl(
                giving_partner_id=giving_partner.id,
                address=gp_address,
                latitude=giving_partner.latitude,
                longitude=giving_partner.longitude,
                api_id=autocomplete_result,
                source="Google",
            )
            try:
                session.add(gp_info)
                session.commit()
                logger.info(f"succesfully processed {giving_partner.name}")
            except SQLAlchemyError as e:
                logger.error(f"sqlalchemy insertion error: {e}")
                raise
            return
    else:
        logger.error(
            "skipping autocomplete check as autocomplete was not toggled on using 'enable_autocomplete'"  # pylint: disable=line-too-long
        )
    try:
        text_search_results = text_search(giving_partner)
    except Exception as e:
        logger.error(f"Error calling google text search API: {e}")
        raise
    if len(text_search_results) > 0:
        # get the topmost result from the text search assuming it is the right GP
        top_result = text_search_results[0]
        if not check_topmost(top_result, giving_partner):
            logger.info(
                f"not processed as the topmost result from text search {top_result["displayName"]["text"]} does not match gp name {giving_partner.name}"  # pylint: disable=line-too-long
            )
            return
        try:
            gp_info2 = gpl(
                giving_partner_id=giving_partner.id,
                address=top_result["formattedAddress"],
                latitude=top_result["location"]["latitude"],
                longitude=top_result["location"]["longitude"],
                api_id=top_result["id"],
                source="Google",
            )
            session.add(gp_info2)
            session.commit()
            logger.info(f"succesfully processed {giving_partner.name}")
        except (SQLAlchemyError, KeyError, TypeError) as e:
            logger.error(f"Insertion failed for {giving_partner.name}: {e}")
            raise
        return
    logger.info(
        "not processed as neither autocomplete check passed nor the topmost result from text search does not match"  # pylint: disable=line-too-long
    )
    return


if "__main__" == __name__:
    main()
