# google_locations
Project that retrieves google locations of GPs

To run this script locally, spin this project up in docker locally through the following steps:

 1. setup environment variables: Run "cp example.env .env" and update the values in .env file
 2. Make sure your MySQL container is already running and connected to the same Docker network as "DOCKER_NETWORK" in the .env file if you're using an external database container
 3. build and run the services using by running the "docker compose up --build -d" command in the path/to/google-locations directory
 4. Then run the script using "docker compose exec google-locations-app python main.py {optional arguments}"

 The optional command line args you can use are:
 1. --id <ID>: If you want to process a specific GP from donee_info table by providing their ID
 2. --enable_autocomplete: processes GPs while utilizing autocomplete API. Autocomplete check is disabled by default.
 3. --disable_cache_check: Disables Redis cache check that checks if a GP has previosuly failed to avoid running them again. The redis cache stores the GP IDs for a month from when they first failed (meaning they were either not found in the google API or the result was not valid). cache_check is True by default


 Examples of ways to run:
 'python main.py', processes multiple GPs at once
 'python main.py --id 479", processes GP with ID 479
 'python main.py --id 479 --enable_autocomplete', processes GP with ID 479 while utilizing the autocomplete API
 'python main.py --enable_autocomplete' processes multiple GPs at once while utilizing the autocomplete API
'python main.py --disable_cache_check --id 479' processes gp 479 regardless of whether it's run failed before (meaning it was either not found in the google API or the result was not valid)