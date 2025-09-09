# Use our base Python image
FROM 211125698795.dkr.ecr.us-east-1.amazonaws.com/base-python:3.12-base
ARG WORKDIR=/srv
ARG USER_NAME=www-data
ARG GROUP_NAME=www-data

# Set the working directory
WORKDIR $WORKDIR

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY --chown=$USER_NAME:$GROUP_NAME . .

# Change the ownership of the working directory to the app user
RUN chown -R $USER_NAME:$GROUP_NAME $WORKDIR