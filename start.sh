#!/bin/bash

# Ensure required environment variables are set for both Mosquitto and TTN
if { [ -z "$MQTT_BROKER" ] || [ -z "$MQTT_PORT" ] || [ -z "$MQTT_TOPIC" ]; } && \
   { [ -z "$TTN_MQTT_BROKER" ] || [ -z "$TTN_MQTT_PORT" ] || [ -z "$TTN_MQTT_TOPIC" ] || \
     [ -z "$TTN_MQTT_USER" ] || [ -z "$TTN_MQTT_PASSWORD" ]; }; then
  echo "Error: Required environment variables for both Mosquitto and TTN are not set."
  echo "Please set the relevant variables for either MQTT (Mosquitto) or TTN."
  exit 1
fi

# Start the MQTT subscriber in the background
nohup python3 mqtt_subscriber.py &

# Get the PORT environment variable
PORT=${PORT:-6969}  # Default to 6969 if PORT is not set

# Start the Flask application using Gunicorn
exec gunicorn --bind 0.0.0.0:$PORT app:app
