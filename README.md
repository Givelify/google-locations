# google_locations
Project that retrieves google locations of GPs

Spin this project up in docker through the following steps:

 1. setup environment variables: "cp example.env .env" and update the values
 2. Make sure your MySQL container is already running and connected to the same Docker network as "DOCKER_NETWORK" in the .env file if you're using an external database container
 3. build and run the services using by running the "docker compose up --build -d" command in the path/to/google-locations directory
 4. Then run the script using "docker compose exec google-locations-app python main.py {optional arguments}"

 The optional command line args you can use are:
 1. --id <ID>: If you want to process a specific GP from donee_info table by providing their ID
 2. --enable_autocomplete: processes GPs while utilizing autocomplete API. Autocomplete check is disabled by default.
 3. --cache_check <Bool>: Enables Redis cache check to see if a GP has previosuly failed to avoid running them again. The redis cache stores the GP IDs for a month from when they first failed. Use '--cache_check IDs cache_check is True by default

