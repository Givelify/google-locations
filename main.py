"""Module that connects to mysql server and performs database operations"""

from sqlalchemy import and_, func, select
from sqlalchemy.exc import SQLAlchemyError

from checks import autocomplete_check, check_topmost
from config import Config
from google_api_calls import text_search
from models import GivingPartnerLocations as gpl
from models import GivingPartners as gp
from models import get_engine, get_session


def main():
    """Main module"""

    try:
        engine = get_engine(
            db_host=Config.DB_HOST,
            db_port=Config.DB_PORT,
            db_user=Config.DB_USER,
            db_password=Config.DB_PASSWORD,
            db_name=Config.DB_NAME,
        )
        # log the success
    except SQLAlchemyError as e:
        print(f"Failed to initialize database engine: {e}")  # error log this
        raise

    active = 1
    unregistered = 0

    query = (
        select(gp)
        .join(gpl, gp.id == gpl.giving_partner_id, isouter=True)
        .where(
            and_(
                gpl.giving_partner_id.is_(None),
                gp.active == active,
                gp.unregistered == unregistered,
                gp.country.isnot(None),
                func.trim(gp.country) != "",
            )
        )
        .limit(5)
    )
    try:
        with get_session(engine) as session:
            # log the success of creating the session
            result = session.scalars(query).all()
            for giving_partner in result:
                print(
                    f"Processing donee_id: {giving_partner.id}, name: {giving_partner.name}, address: {giving_partner.address}, {giving_partner.city}, {giving_partner.state}, {giving_partner.country}"  # pylint: disable=line-too-long
                )  # log this
                try:
                    process_gp(giving_partner, session)
                except (KeyError, TypeError) as e:
                    print(f"Error in process_gp(): {e}")  # error log this
    except SQLAlchemyError as e:
        print(f"failed to create session: {e}")  # error log this
    finally:
        engine.dispose()


def process_gp(giving_partner, session):
    """Module that processes each GP"""
    autocomplete_result = autocomplete_check(giving_partner)
    if autocomplete_result:
        gp_address = f"{giving_partner.address}, {giving_partner.city}, {giving_partner.state}, {giving_partner.country}"
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
            print(
                f"succesfully processed {giving_partner.name}"
            )  # log this sucessfull processing
        except SQLAlchemyError as e:
            print(f"sqlalchemy insertion error: {e}")  # error log this
            raise
        return
    try:
        text_search_results = text_search(giving_partner)
    except RuntimeError as e:
        print(f"{e}")  # error log this
        raise
    if len(text_search_results) > 0:
        # get the topmost result from the text search assuming it is the right GP
        top_result = text_search_results[0]
        if not check_topmost(top_result, giving_partner):
            print(
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
            print(
                f"succesfully processed {giving_partner.name}"
            )  # log this sucessful processing
        except (SQLAlchemyError, KeyError, TypeError) as e:
            print(f"Insertion failed for {giving_partner.name}: {e}")  # log error
            raise
        return
    print(
        "not processed as neither autocomplete check passed nor the topmost result from text search does not match"  # pylint: disable=line-too-long
    )  # log the failure to process the GP
    return


if "__main__" == __name__:
    main()
