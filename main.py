"""Module that connects to mysql server"""

from mysql.connector import connect

from checks import autocomplete_check
from google_api_calls import text_search

connection = connect(host="127.0.0.1", user="givelify", passwd="givelify", port="13306")


mycursor = connection.cursor(dictionary=True)


def main():
    """Main module"""
    # pull the non - processed GPs from the database
    query = """
    SELECT a.*
FROM givelify.donee_info AS a
LEFT JOIN platform.giving_partner_locations AS b
    ON a.donee_id = b.giving_partner_id
WHERE b.giving_partner_id IS NULL
   OR (b.giving_partner_id IS NOT NULL AND a.active = %s AND a.unregistered = %s) LIMIT 1;
    """
    vals = (1, 0)

    mycursor.execute(query, vals)

    data = mycursor.fetchall()

    for gp in data:
        print(
            f"Processing donee_id: {gp['donee_id']}, name: {gp['name']}, address: {gp["address"]}"
        )
        process_gp(gp)


def process_gp(gp):
    """Module that processes each GP"""
    autocomplete_result = autocomplete_check(gp)
    if autocomplete_result[0]:
        write_query = (
            "INSERT INTO platform.giving_partner_locations "
            "(giving_partner_id, phone_number, address, latitude, longitude, api_id) "
            "VALUES (%s, %s, %s, %s, %s, %s)"
        )
        gp_address = (
            gp["address"]
            + ", "
            + gp["city"]
            + ", "
            + gp["state"]
            + ", "
            + gp["country"]
        )  # for now just add from done_info table, but in future add code to pull city, state and country from autocomplete result to help with cases when those fields are empty or inaccurate in donee_info
        vals = (
            gp["donee_id"],
            gp["phone"],
            gp_address,
            gp["donee_lat"],
            gp["donee_lon"],
            autocomplete_result[1],
            # 1, # valid is set to 1 as verified the address in our DB with the autocomplete API
            # 1 # same_address is set to 1 as its the same as one returned by the autocomplete API
        )

        mycursor.execute(write_query, vals)

        print("processed")

        return True  # processed successfully
    # text_search_results = text_search(gp)
    # if len(text_search_results) > 0:
    #     # get the topmost result from the text search assuming it is the right GP
    #     top_result = text_search_results[0]
    #     valid = check_gp(top_result, gp)
    #     if not valid:
    #         return False
    #     else:
    #         write_query = "INSERT INTO platform.giving_partner_locations (giving_patnter_id, phone_number, address, latitude, longitude, api_id) VALUES (%s, %s, %s, %s, %s, %s)"
    #         vals = (
    #             gp['donee_id'],
    #             gp['phone_number'],
    #             gp['address'],
    #             gp['latitude'],
    #             gp['longitude'],
    #             gp['api_id'],
    #             # 1, # valid is set to 1 as we couldn't verify the address
    #             # 0 # same_address is set to 0 as its not the same as one returned by the autocomplete API
    #     )
    # else:
    #     return False
    print("not processed")
    return False


if "__main__" == __name__:
    main()


connection.commit()

mycursor.close()
connection.close()
