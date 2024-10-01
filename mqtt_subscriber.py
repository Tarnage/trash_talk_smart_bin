import paho.mqtt.client as mqtt
import os
import json
import base64
from app import app, db, SmartBinData
import logging
import sys
from threading import Thread

# Setup logging to print to stdout
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# MQTT configuration from environment variables
mqtt_broker = os.environ.get('MQTT_BROKER')
mqtt_port = int(os.environ.get('MQTT_PORT', 1883))  # Default to 1883 if not provided
mqtt_user = os.environ.get('MQTT_USER')
mqtt_password = os.environ.get('MQTT_PASSWORD')
mqtt_topic = os.environ.get('MQTT_TOPIC')

# Log environment variables to confirm they are being loaded correctly
logging.debug(f"MQTT Broker: {mqtt_broker}")
logging.debug(f"MQTT Port: {mqtt_port}")
logging.debug(f"MQTT Topic: {mqtt_topic}")
logging.debug(f"MQTT User: {mqtt_user}")

# Properties to be stored in the database
PROPERTIES = [
    "bin_id", "latitude", "longitude", "collection_frequency_per_month",
    "average_collection_time_days", "tilt_status", "fill_level_percentage",
    "temperature_celsius", "displacement", "days_since_last_emptied",
    "communication_status", "battery_level_percentage"
]

def decode_payload(payload):
    try:
        message = json.loads(payload)
        # Decode the base64 payload
        decoded_bytes = base64.b64decode(message['downlink_queued']['frm_payload']).decode('utf-8')
        logging.debug(f"Decoded bytes: {decoded_bytes}")

        # Remove any extraneous characters (like '-n') before parsing
        if decoded_bytes.startswith('-n '):
            decoded_bytes = decoded_bytes[3:]  # Remove the '-n ' prefix

        return json.loads(decoded_bytes)
    except json.JSONDecodeError as e:
        logging.error(f"JSON decoding error: {e} - payload: {decoded_bytes}")
        return None
    except Exception as e:
        logging.error(f"Error decoding payload: {e}")
        return None

def on_message(client, userdata, message):
    # Log the received raw MQTT message
    logging.debug(f"Received raw MQTT message: {message.payload}")
    
    # Decode payload
    payload = decode_payload(message.payload)
    
    if payload:
        logging.debug(f"Decoded payload: {payload}")
    else:
        logging.debug("Payload could not be decoded.")
        return

    with app.app_context():
        bin_id = payload.get('bin_id')
        if not bin_id:
            logging.debug("Missing bin_id in payload.")
            return
        
        logging.debug(f"Looking up bin_id: {bin_id}")
        existing_bin = SmartBinData.query.filter_by(bin_id=bin_id).first()
        if existing_bin:
            logging.debug(f"Updating existing bin with ID: {bin_id}")
            for key, value in payload.items():
                if key in PROPERTIES:
                    logging.debug(f"Setting {key} to {value} for bin ID {bin_id}")
                    setattr(existing_bin, key, value)
            logging.debug(f"Updated bin: {existing_bin.__dict__}")
        else:
            logging.debug(f"Creating new bin with ID: {bin_id}")
            new_bin = SmartBinData(**{k: v for k, v in payload.items() if k in PROPERTIES})
            db.session.add(new_bin)

        try:
            db.session.commit()
            logging.debug("Data inserted/updated successfully.")
        except Exception as e:
            logging.error(f"Error committing data to the database: {e}")
            db.session.rollback()  # Rollback session in case of error

def on_connect(client, userdata, flags, reason_code, properties=None):
    logging.debug(f"Connection result code: {reason_code}")
    
    if reason_code == 0:
        logging.debug(f"Connected to broker at {mqtt_broker}:{mqtt_port}")
        # Attempt to subscribe and check result
        result, mid = client.subscribe(mqtt_topic)
        if result == mqtt.MQTT_ERR_SUCCESS:
            logging.debug(f"Subscribed to {mqtt_topic} successfully.")
        else:
            logging.error(f"Failed to subscribe to {mqtt_topic}, result code: {result}")
    else:
        logging.error(f"Failed to connect, reason code: {reason_code}")

def mqtt_loop():
    client = mqtt.Client()

    client.on_message = on_message
    client.on_connect = on_connect

    # Enable logging for debugging purposes
    client.enable_logger()

    if mqtt_user and mqtt_password:
        client.username_pw_set(mqtt_user, mqtt_password)

    logging.debug("Connecting to broker...")
    try:
        client.connect(mqtt_broker, mqtt_port, 60)
    except Exception as e:
        logging.error(f"Unable to connect to MQTT broker: {e}")
        return

    client.loop_forever()

def start_mqtt():
    mqtt_thread = Thread(target=mqtt_loop)
    mqtt_thread.daemon = True  # Ensures this thread will be killed when the main thread exits
    mqtt_thread.start()

# Modify the app.run to ensure MQTT starts properly
if __name__ != "__main__":
    logging.debug("Starting MQTT client...")
    start_mqtt()

# If running the app directly, start Flask and MQTT
if __name__ == "__main__":
    logging.debug("Starting Flask app...")
    start_mqtt()
    app.run(host='0.0.0.0', port=5000)
