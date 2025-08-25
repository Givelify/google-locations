"""Module that connects to mysql server and performs database operations"""

from checks import autocomplete_check, text_search_similarity_check
from config import Config
from google_api_calls import text_search, geocoding_reverse_api
from helper import (
    get_giving_partners,
    parse_args,
    process_autocomplete_results,
    process_text_search_results,
    fetch_gp_locations,
    extract_outlines
)
from models import get_engine, get_session
from shapely.geometry import MultiPolygon, Polygon

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
    except SystemExit as e:
        logger.error(
            "Parsing command-line arguments failed.", value={"exception": str(e)}
        )
        raise
    except Exception as e:
        logger.error(
            "Failed to initialize database engine.", value={"exception": str(e)}
        )
        raise

    try:
        with get_session(engine) as session:
            result = get_giving_partners(session, args.id)
            if len(result) == 0:
                logger.info(
                    "No Giving Partner(s) to process",
                    value={"giving_partner_id": str(args.id)},
                )
                return
            for giving_partner in result:
                try:
                    process_gp(
                        giving_partner,
                        session,
                        args.enable_autocomplete,
                    )
                except Exception as e:
                    logger.error(
                        "Error processing giving partner",
                        value={
                            "exception": str(e),
                            "giving_partner_id": str(giving_partner.id),
                        },
                    )
    except Exception as e:
        logger.error("Failed to update with Google location data", value=str(e))
    finally:
        engine.dispose()


def process_gp(giving_partner, session, enable_autocomplete=False):
    """Module that processes each GP"""
    logger.info(
        "Processing Giving Partner",
        value={
            "giving_partner_id": str(giving_partner.id),
        },
    )

    # Autocomplete checks if Google has matching location details.
    # If so, we skip the more expensive text search call.
    if enable_autocomplete:
        place_id = autocomplete_check(giving_partner)
        if place_id and process_autocomplete_results(session, giving_partner, place_id):
            logger.info(
                "Autocomplete process successful for GP",
                value={
                    "giving_partner_id": str(giving_partner.id),
                    "status": "success",
                },
            )
            return

    text_search_results = text_search(giving_partner)
    if not len(text_search_results) > 0:
        logger.info(
            "No text search results for GP",
            value={
                "giving_partner_id": str(giving_partner.id),
            },
        )
        return
    top_text_search_result = text_search_results[0]
    if text_search_similarity_check(giving_partner, top_text_search_result):
        process_text_search_results(session, giving_partner, top_text_search_result)
        logger.info(
            "Text search process successful for GP",
            value={"giving_partner_id": str(giving_partner.id), "status": "success"},
        )
    else:
        logger.info(
            "Top most text search result is not viable for GP",
            value={
                "giving_partner_id": str(giving_partner.id),
                "top_text_search_result": top_text_search_result,
            },
        )

    return

def get_connection():
    try:
        args = parse_args()
        engine = get_engine(
            db_host=Config.DB_HOST,
            db_port=Config.DB_PORT,
            db_user=Config.DB_USER,
            db_password=Config.DB_PASSWORD,
            db_name=Config.DB_NAME,
        )
        return engine
    except SystemExit as e:
        logger.error(
            "Parsing command-line arguments failed.", value={"exception": str(e)}
        )
        raise
    except Exception as e:
        logger.error(
            "Failed to initialize database engine.", value={"exception": str(e)}
        )
        raise

def main2():
    gp_ids = Config.GP_IDS
    engine = get_connection()

    logger.debug(f"Engine: {engine}")
    try:
        print(f"Giving-Partner-ID, Google Outlines")
        with get_session(engine) as session:
            # logger.info(f"Session: {session}")
            results = fetch_gp_locations(session)
            for giving_partner in results:
                logger.debug(f"Giving Partner: {giving_partner.id}, {giving_partner.latitude}, {giving_partner.longitude}")
                
                data = geocoding_reverse_api(giving_partner.latitude, giving_partner.longitude)
                results = data.get("results", [])
                # print(f"results: {results[0]}")
                if results and len(results) > 0:
                    building_outlines = extract_outlines(results)
                    print(f'{giving_partner.id},"{building_outlines}"')
    except Exception as e:
        logger.error(f"Failed to update with Google location data: {e}")
    finally:
        engine.dispose()

    

if "__main__" == __name__:    
    # if False:
    if not Config.BUILDING_OUTLINES_ONLY:
        main()
    else:
        main2()
