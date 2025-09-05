# google_locations
Project that retrieves google locations of GPs
Instructions on how to run the script:
1. Setup the "platform" database locally by the running the migrations for it: https://github.com/Givelify/platform-db-migrator
2. Copy the contents of .env.example file and add database credentials and google api key to run this project
3. Setup a virtual environment
4. Run 'pip install -r requirements.txt' in terminal
5. Run the main script using "python3 -m app.main" 
    - To process specific GPs from the donee_info table, set their IDs in the GP_IDS environment variable.
    - To enable the autocomplete check (default: true), set ENABLE_AUTOCOMPLETE=true.
    - To process only building outlines (default: true), set BUILDING_OUTLINES_ONLY=true.
