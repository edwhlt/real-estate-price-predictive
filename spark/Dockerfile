# Use the jupyter/all-spark-notebook:latest image as the base image
FROM jupyter/all-spark-notebook:latest

# Install required Python packages
RUN pip install googlemaps

# Set the working directory
WORKDIR /home/jovyan

# Copy the model directory and streaming_predictive.py script into the container
COPY streaming_predictive.py ./streaming_predictive.py
COPY model ./model

# Run the spark-submit command