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

# Properties to be stored in the database
PROPERTIES = [
    "bin_id", "latitude", "longitude", "collection_frequency_per_month",
    "average_collection_time_days", "tilt_status", "fill_level_percentage",
    "temperature_celsius", "displacement", "days_since_last_emptied",
    "communication_status", "battery_level_percentage"
]

# Configuration for multiple brokers, including TTN and Mosquitto
mqtt_brokers = [
    {
        "host": os.environ.get('MQTT_BROKER'),
        "port": int(os.environ.get('MQTT_PORT', 1883)),
        "topic": os.environ.get('MQTT_TOPIC'),
        "username": None,  # No authentication for Mosquitto test server
        "password": None,
        "is_ttn": False  # Indicate if broker is TTN (for decoding base64)
    },
    {
        "host": os.environ.get('TTN_MQTT_BROKER'),
        "port": int(os.environ.get('TTN_MQTT_PORT', 1883)),
        "topic": os.environ.get('TTN_MQTT_TOPIC'),
        "username": os.environ.get('TTN_MQTT_USER'),
        "password": os.environ.get('TTN_MQTT_PASSWORD'),
        "is_ttn": True  # TTN uses base64 encoded payloads
    }
]

# Log environment variables to confirm they are being loaded correctly
for broker in mqtt_brokers:
    logging.debug(f"MQTT Broker: {broker['host']}")
    logging.debug(f"MQTT Port: {broker['port']}")
    logging.debug(f"MQTT Topic: {broker['topic']}")
    if broker['username']:
        logging.debug(f"MQTT User: {broker['username']}")

def decode_payload(payload):
    try:
        message = json.loads(payload)
        # Decode the base64 payload for TTN messages
        decoded_bytes = base64.b64decode(message['downlink_queued']['frm_payload']).decode('utf-8')
        logging.debug(f"Decoded bytes: {decoded_bytes}")

        # Remove any extraneous characters (like '-n') before parsing
        if decoded_bytes.startswith('-n '):
            decoded_bytes = decoded_bytes[3:]  # Remove the '-n ' prefix

        return json.loads(decoded_bytes)
    except json.JSONDecodeError as e:
        logging.error(f"JSON decoding error: {e} - payload: {payload}")
        return None
    except Exception as e:
        logging.error(f"Error decoding payload: {e}")
        return None

def on_message(client, userdata, message, is_ttn=False):
    logging.debug(f"Received raw MQTT message: {message.payload}")

    try:
        payload = json.loads(message.payload)
        logging.debug(f"Decoded JSON payload: {payload}")

        if is_ttn and 'downlink_queued' in payload and 'frm_payload' in payload['downlink_queued']:
            # Handle TTN base64-encoded payload
            decoded_payload = decode_payload(message.payload)
            if decoded_payload:
                payload = decoded_payload
                logging.debug(f"Decoded TTN payload: {payload}")
    except json.JSONDecodeError:
        logging.debug("Received plain text message.")
        plain_text_message = message.payload.decode('utf-8')
        payload = {'message': plain_text_message}

    if payload:
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
                db.session.rollback()

def on_connect(client, userdata, flags, reason_code, broker_config):
    logging.debug(f"Connection result code: {reason_code}")
    
    if reason_code == 0:
        logging.debug(f"Connected to broker at {broker_config['host']}:{broker_config['port']}")
        result, mid = client.subscribe(broker_config['topic'])
        if result == mqtt.MQTT_ERR_SUCCESS:
            logging.debug(f"Subscribed to {broker_config['topic']} successfully.")
        else:
            logging.error(f"Failed to subscribe to {broker_config['topic']}, result code: {result}")
    else:
        logging.error(f"Failed to connect, reason code: {reason_code}")

def mqtt_loop(broker_config):
    client = mqtt.Client()

    # Attach handlers
    client.on_message = lambda client, userdata, message: on_message(client, userdata, message, is_ttn=broker_config["is_ttn"])
    client.on_connect = lambda client, userdata, flags, reason_code: on_connect(client, userdata, flags, reason_code, broker_config)

    client.enable_logger()

    if broker_config['username'] and broker_config['password']:
        client.username_pw_set(broker_config['username'], broker_config['password'])

    logging.debug(f"Connecting to broker {broker_config['host']} on port {broker_config['port']}...")
    try:
        client.connect(broker_config['host'], broker_config['port'], 60)
    except Exception as e:
        logging.error(f"Unable to connect to MQTT broker: {e}")
        return

    client.loop_forever()

def start_mqtt():
    for broker in mqtt_brokers:
        mqtt_thread = Thread(target=mqtt_loop, args=(broker,))
        mqtt_thread.daemon = True  # Ensure the thread is killed when the main thread exits
        mqtt_thread.start()

# Modify the app.run to ensure MQTT starts properly
if __name__ != "__main__":
    logging.debug("Starting MQTT clients for multiple brokers...")
    start_mqtt()

# If running the app directly, start Flask and MQTT
if __name__ == "__main__":
    logging.debug("Starting Flask app and MQTT clients...")
    start_mqtt()
    app.run(host='0.0.0.0', port=5000)
