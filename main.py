"""Module that connects to mysql server and performs database operations"""

import redis
from redis.exceptions import RedisError
from sqlalchemy import and_, func, select
from sqlalchemy.exc import SQLAlchemyError

from checks import autocomplete_check
from config import Config
from google_api_calls import text_search
from helper import autocomplete_branch, parse_args, text_search_branch
from models import GivingPartners as gp
from models import GoogleGivingPartnerLocations as gpl
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


def main():
    """Main module"""
    r = redis.Redis(
        host="localhost", port=6379, db=0  # The default Redis database index
    )
    try:
        r = redis.Redis(
            host="localhost", port=6379, db=0  # The default Redis database index
        )
        args = parse_args()

        engine = get_engine(
            db_host=Config.DB_HOST,
            db_port=Config.DB_PORT,
            db_user=Config.DB_USER,
            db_password=Config.DB_PASSWORD,
            db_name=Config.DB_NAME,
        )
        logger.info("Successfully created the MySQL Engine")
    except SystemExit:
        logger.error("parsing args failed")
        raise
    except SQLAlchemyError as e:
        logger.error(f"Failed to initialize database engine: {e}")  # error log this
        raise
    except RedisError as e:
        logger.error(f"Redis Connection Error: {e}")
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
                    f"No active and registered GP exists with the provided id: {args.id} in the donee_info / giving patners table"  # pylint: disable=line-too-long
                )
                return
            for giving_partner in result:
                logger.info(
                    f"Processing donee_id: {giving_partner.id}, name: {giving_partner.name}, address: {giving_partner.address}, {giving_partner.city}, {giving_partner.state}, {giving_partner.country}"  # pylint: disable=line-too-long
                )
                try:
                    if args.cache_check:
                        if r.sismember("Non_processed_GPs", giving_partner.id):
                            logger.info(
                                f"""GP ID: {giving_partner.id} failed run before, can't process it for a month from its initial run.
                                If you want to run it anyway, run 'python main.py --id {{ID}} --cache_check=False'"""  # pylint: disable=line-too-long
                            )
                            continue
                    process_gp(
                        giving_partner,
                        session,
                        autocomplete_toggle=args.enable_autocomplete,
                    )
                except Exception as e:  # pylint: disable=broad-exception-caught
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
            autocomplete_branch(giving_partner, session, autocomplete_result)
            return
    else:
        logger.info(
            "skipping autocomplete check as autocomplete was not toggled on using 'enable_autocomplete'"  # pylint: disable=line-too-long
        )
    text_search_results = text_search(giving_partner)
    if len(text_search_results) > 0:
        text_search_branch(giving_partner, text_search_results, session)
        return
    logger.info(
        "not processed as neither autocomplete check passed nor the topmost result from text search does not match"  # pylint: disable=line-too-long
    )
    return


if "__main__" == __name__:
    main()
