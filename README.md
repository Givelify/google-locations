# google_locations
Project that retrieves google locations of GPs
Instructions on how to run the script:
1. Setup the "platform" database locally by the running the migrations for it: https://github.com/Givelify/platform-db-migrator
2. Copy the contents of .env.example file and add database credentials and google api key to run this project
3. Setup a virtual environment
4. Run 'pip install -r requirements.txt' in terminal
5. Run the main script using "python main.py" if you want to process multiple GPs in the donee_info table or 
 - "python main.py --id {ID}" if you want to process a specific GP from donee_info table by providing their ID.
 - If you want autocomplete check enabled use the additional parameter "--enable_autocomplete" in the command. Autocomplete check is disabled by default.
 Examples of ways to run:
 'python main.py',
 'python main.py --gp_id=479",
 'python main.py --gp_id=479 --enable_autocomplete',
 'python main.py --enable_autocomplete'
