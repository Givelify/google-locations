"""Module that connects to mysql server"""

from mysql.connector import connect

from checks import autocomplete_check, check_topmost
from google_api_calls import text_search


def main():
    """Main module"""
    connection = connect(
        host="127.0.0.1", user="givelify", passwd="givelify", port="13306"
    )

    mycursor = connection.cursor(dictionary=True)
    # pull the non - processed GPs from the database
    query = """
    SELECT a.*
FROM givelify.donee_info AS a
LEFT JOIN platform.giving_partner_locations AS b
    ON a.donee_id = b.giving_partner_id
WHERE b.giving_partner_id IS NULL
   OR (b.giving_partner_id IS NOT NULL AND a.active = %s AND a.unregistered = %s) LIMIT 5;
    """
    vals = (1, 0)

    mycursor.execute(query, vals)

    data = mycursor.fetchall()  # pylint: disable=redefined-outer-name

    for gp in data:
        print(
            f"Processing donee_id: {gp['donee_id']}, name: {gp['name']}, address: {gp["address"]}"
        )
        process_gp(gp, mycursor)
    connection.commit()

    mycursor.close()
    connection.close()


def process_gp(gp, cursor):
    """Module that processes each GP"""
    autocomplete_result = autocomplete_check(gp)
    # autocomplete_result is a tuple of type (bool, place_id)
    if autocomplete_result[0]:
        write_query = (
            "INSERT INTO platform.giving_partner_locations "
            "(giving_partner_id, giving_partner_name, phone_number, address, latitude, longitude, api_id) "  # pylint: disable=line-too-long
            "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        )
        gp_address = (
            gp["address"]
            + ", "
            + gp["city"]
            + ", "
            + gp["state"]
            + ", "
            + gp["country"]
        )  # for now just add from done_info table, but in future add code to pull city, state and country from autocomplete result to help with cases when those fields are empty or inaccurate in donee_info # pylint: disable=line-too-long
        vals = (
            gp["donee_id"],
            gp["name"],
            gp["phone"],
            gp_address,
            gp["donee_lat"],
            gp["donee_lon"],
            autocomplete_result[1],
        )

        cursor.execute(write_query, vals)

        print("processed")

        return True  # processed successfully, log success
    text_search_results = text_search(gp)
    if len(text_search_results) > 0:
        # get the topmost result from the text search assuming it is the right GP
        top_result = text_search_results[0]
        valid = check_topmost(top_result, gp)
        if not valid:
            print(
                f"not processed as the topmost result from text search {top_result["displayName"]["text"]} does not match gp name {gp["name"]}"  # pylint: disable=line-too-long
            )
            return False
        write_query = "INSERT INTO platform.giving_partner_locations (giving_partner_id, giving_partner_name, phone_number, address, latitude, longitude, api_id) VALUES (%s, %s, %s, %s, %s, %s, %s)"  # pylint: disable=line-too-long
        vals = (
            gp["donee_id"],
            top_result["displayName"]["text"],
            gp[
                "phone"
            ],  # for now just do ph no from our db, but if we get ph no from api use that as public facing one  # pylint: disable=line-too-long
            top_result["formattedAddress"],
            top_result["location"]["latitude"],
            top_result["location"]["longitude"],
            top_result["id"],
        )
        cursor.execute(write_query, vals)
        return True
    print(
        "not processed as neither autocomplete check passed nor the topmost result from text search does not match"  # pylint: disable=line-too-long
    )  # log the failure to process the GP
    return False


if "__main__" == __name__:
    main()
