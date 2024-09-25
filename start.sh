#!/bin/bash
# Start Flask app and MQTT subscriber
python3 app.py &
python3 mqtt_subscriber.py