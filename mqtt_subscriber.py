import paho.mqtt.client as mqtt
import os
import json
import base64
from app import app, db, SmartBinData
import logging
import sys

# Setup logging to print to stdout
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# MQTT configuration from environment variables
mqtt_broker = os.environ.get('MQTT_BROKER')
mqtt_port = int(os.environ.get('MQTT_PORT'))
mqtt_user = os.environ.get('MQTT_USER')
mqtt_password = os.environ.get('MQTT_PASSWORD')
mqtt_topic = os.environ.get('MQTT_TOPIC')

# Print environment variables to confirm they are being loaded correctly
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
        decoded_bytes = base64.b64decode(message['downlink_queued']['frm_payload']).decode('utf-8')
        logging.debug(f"Decoded bytes: {decoded_bytes}")
        return json.loads(decoded_bytes)
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

        existing_bin = SmartBinData.query.filter_by(bin_id=bin_id).first()
        if existing_bin:
            for key, value in payload.items():
                if key in PROPERTIES:
                    setattr(existing_bin, key, value)
        else:
            new_bin = SmartBinData(**{k: v for k, v in payload.items() if k in PROPERTIES})
            db.session.add(new_bin)

        db.session.commit()
        logging.debug("Data inserted/updated successfully.")

def on_connect(client, userdata, flags, reason_code, properties=None):
    logging.debug(f"Connection result code: {reason_code}")
    
    if reason_code == 0:
        logging.debug(f"Connected to broker at {mqtt_broker}:{mqtt_port}")
        # Attempt to subscribe and check result
        result, mid = client.subscribe(mqtt_topic)
        if result == mqtt.MQTT_ERR_SUCCESS:
            logging.debug(f"Subscribed to {mqtt_topic} successfully.")
        else:
            logging.debug(f"Failed to subscribe to {mqtt_topic}, result code: {result}")
    else:
        logging.debug(f"Failed to connect, reason code: {reason_code}")

def init_mqtt():
    client = mqtt.Client()

    client.on_message = on_message
    client.on_connect = on_connect

    # Enable logging for debugging purposes
    client.enable_logger()

    if mqtt_user and mqtt_password:
        client.username_pw_set(mqtt_user, mqtt_password)

    logging.debug("Connecting to broker...")
    client.connect(mqtt_broker, mqtt_port, 60)
    client.loop_start()

if __name__ == "__main__":
    logging.debug("Initializing MQTT client...")
    init_mqtt()
