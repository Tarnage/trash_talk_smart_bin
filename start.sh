#!/bin/bash
# Start the MQTT subscriber
python mqtt_subscriber.py &

# Start the Flask app using Gunicorn
exec gunicorn --bind 0.0.0.0:6969 app:app
