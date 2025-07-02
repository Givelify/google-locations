# google_locations
Project that retrieves google locations of GPs
Instructions on how to run the script:
1. Setup the "platform" database locally by the running the migrations for it: https://github.com/Givelify/platform-db-migrator
2. Copy the contents of .env.example file and add database credentials and google api key to run this project
3. Setup a virtual environment
4. Run 'pip install -r requirements.txt' in terminal
5. Run the main script using "python main.py" if you want to process an arbitrary amount of GPs in the donee_info table or 
"python main.py --id {ID}" if you want to process a specific GP from donee_info table by providing their ID.