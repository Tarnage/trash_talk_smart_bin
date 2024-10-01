#!/bin/bash

# Ensure required environment variables are set
if [ -z "$MQTT_BROKER" ] || [ -z "$MQTT_PORT" ] || [ -z "$MQTT_USER" ] || [ -z "$MQTT_PASSWORD" ] || [ -z "$MQTT_TOPIC" ]; then
  echo "Error: Required environment variables are not set."
  echo "Please set MQTT_BROKER, MQTT_PORT, MQTT_USER, MQTT_PASSWORD, and MQTT_TOPIC."
  exit 1
fi

# Start the MQTT subscriber in the background
nohup python mqtt_subscriber.py &

# Get the PORT environment variable
PORT=${PORT:-6969}  # Default to 6969 if PORT is not set

# Start the Flask application using Gunicorn
exec gunicorn --bind 0.0.0.0:$PORT app:app
