# google_locations
Project that retrieves google locations of GPs
Instructions on how to run the script:
1. Setup the "platform" database locally by the running the migrations for it: https://github.com/Givelify/platform-db-migrator
2. Copy the contents of .env.example file and add database credentials and google api key to run this project
3. Setup a virtual environment
4. Run 'pip install -r requirements.txt' in terminal
5. Run the scripts using:
    - "python3 -m app.scripts.outlines" 
        - To process specific GPs from the donee_info table, set their IDs in the GP_IDS environment variable.
    - "python3 -m app.scripts.donee_geocoder" 
    
# donee_geocoder
This script replaces the existing donee_geocoder service and is intended to run as a cron job. Its purpose is to populate coordinates for newly ingested GPs. Unlike the old version, which used LocationIQ, this script retrieves coordinates from the Google API. Additionally, it can fetch and store building outlines for any GP, since the Google API provides that data.

# outlines
This script supports the SE in_building pilot. It updates or inserts building outlines from Google for the specific GPs defined in the GP_IDS environment variable.
