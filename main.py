"""Module that connects to mysql server and performs database operations"""

from sqlalchemy.exc import SQLAlchemyError

from checks import autocomplete_check
from config import Config
from google_api_calls import text_search
from helper import (
    autocomplete_branch,
    get_giving_partners,
    parse_args,
    text_search_branch,
)
from models import get_engine, get_session

logger = Config.logger


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
        logger.info("Successfully created the MySQL Engine")
    except SystemExit:
        logger.error("parsing args failed")
        raise
    except Exception as e:
        logger.error(f"Failed to initialize database engine: {e}")  # error log this
        raise

    try:
        with get_session(engine) as session:
            logger.info("MySQL Session succesflly created")
            result = get_giving_partners(args.id, session)
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
        text_search_success = text_search_branch(
            giving_partner, text_search_results, session
        )
        if text_search_success:
            return
    logger.info(
        "not processed as neither autocomplete check passed nor the text search API returned any valid results"  # pylint: disable=line-too-long
    )
    return


if "__main__" == __name__:
    main()
