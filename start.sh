#!/bin/bash
# Start the MQTT subscriber
python mqtt_subscriber.py &

# Get the PORT environment variable
PORT=${PORT:-6969}  # Default to 6969 if PORT is not set

# Start the Flask application using Gunicorn
exec gunicorn --bind 0.0.0.0:$PORT app:app
