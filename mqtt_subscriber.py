import paho.mqtt.client as mqtt
import os
import json
import base64
import logging
import sys
from threading import Thread
from app import create_app, db, SmartBinData

app = create_app()

# Setup logging to print to stdout
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# MQTT configuration from environment variables (Mosquitto)
mqtt_broker = os.environ.get('MQTT_BROKER')
mqtt_port = int(os.environ.get('MQTT_PORT', 1883))  # Default to 1883 if not provided
mqtt_user = os.environ.get('MQTT_USER')
mqtt_password = os.environ.get('MQTT_PASSWORD')
mqtt_topic = os.environ.get('MQTT_TOPIC')

# MQTT configuration from environment variables (TTN)
ttn_broker = os.environ.get('TTN_MQTT_BROKER')
ttn_port = int(os.environ.get('TTN_MQTT_PORT', 1883))  # Default to 1883 if not provided
ttn_user = os.environ.get('TTN_MQTT_USER')
ttn_password = os.environ.get('TTN_MQTT_PASSWORD')
ttn_topic = os.environ.get('TTN_MQTT_TOPIC')

# Log environment variables to confirm they are being loaded correctly
logging.debug(f"MQTT Broker: {mqtt_broker}")
logging.debug(f"MQTT Port: {mqtt_port}")
logging.debug(f"MQTT Topic: {mqtt_topic}")
logging.debug(f"MQTT User: {mqtt_user}")

logging.debug(f"TTN Broker: {ttn_broker}")
logging.debug(f"TTN Port: {ttn_port}")
logging.debug(f"TTN Topic: {ttn_topic}")
logging.debug(f"TTN User: {ttn_user}")

# Properties to be stored in the database
PROPERTIES = [
    "bin_id", "latitude", "longitude", "collection_frequency_per_month",
    "average_collection_time_days", "tilt_status", "fill_level_percentage",
    "temperature_celsius", "displacement", "days_since_last_emptied",
    "communication_status", "battery_level_percentage"
]

def is_valid_payload(payload):
    """Validate the payload fields and types."""
    if 'bin_id' not in payload or not payload['bin_id']:
        logging.debug("Missing or empty bin_id in payload.")
        return False

    # Convert bin_id to string if it's not already
    payload['bin_id'] = str(payload['bin_id'])

    # Check and convert numeric fields
    numeric_fields = ['fill_level_percentage', 'battery_level_percentage', 'temperature_celsius']
    for field in numeric_fields:
        if field in payload:
            try:
                value = float(payload[field])
                if field.endswith('percentage') and not (0 <= value <= 100):
                    logging.debug(f"Invalid {field}: {value}")
                    return False
                if field == 'temperature_celsius' and not (-40 <= value <= 85):
                    logging.debug(f"Invalid {field}: {value}")
                    return False
                payload[field] = value
            except ValueError:
                logging.debug(f"Invalid {field}: {payload[field]}")
                return False

    return True

def decode_payload(payload):
    """Decode the incoming payload."""
    try:
        message = json.loads(payload)
        frm_payload = message.get('downlink_queued', {}).get('frm_payload')
        if not frm_payload:
            logging.error("No frm_payload found in the payload.")
            return None

        decoded_bytes = base64.b64decode(frm_payload).decode('utf-8')
        logging.debug(f"Decoded bytes: {decoded_bytes}")

        if decoded_bytes.startswith('-n '):
            decoded_bytes = decoded_bytes[3:]

        decoded_json = json.loads(decoded_bytes)
        
        # Convert numeric values to float
        numeric_fields = ['fill_level_percentage', 'battery_level_percentage', 'temperature_celsius']
        for field in numeric_fields:
            if field in decoded_json:
                decoded_json[field] = float(decoded_json[field])
        
        return decoded_json
    except json.JSONDecodeError as e:
        logging.error(f"JSON decoding error: {e} - payload: {payload}")
        return None
    except Exception as e:
        logging.error(f"Error decoding payload: {e}")
        return None

def on_message(client, userdata, message):
    """Handle incoming MQTT messages."""
    logging.debug(f"Received raw MQTT message: {message.payload}")

    try:
        payload = json.loads(message.payload)
        logging.debug(f"Decoded JSON payload: {payload}")

        if 'downlink_queued' in payload and 'frm_payload' in payload['downlink_queued']:
            frm_payload = payload['downlink_queued']['frm_payload']
            decoded_payload = base64.b64decode(frm_payload).decode('utf-8')
            logging.debug(f"Decoded frm_payload: {decoded_payload}")

            if decoded_payload.startswith('-n '):
                decoded_payload = decoded_payload[3:]
            payload = json.loads(decoded_payload)
        else:
            logging.debug("No frm_payload found in the message.")

    except json.JSONDecodeError:
        logging.debug("Received plain text message.")
        plain_text_message = message.payload.decode('utf-8')
        payload = {'message': plain_text_message}

    if payload and is_valid_payload(payload):
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

def on_connect(client, userdata, flags, reason_code, properties=None):
    """Handle connection to the MQTT broker."""
    logging.debug(f"Connection result code: {reason_code}")
    if reason_code == 0:
        logging.debug(f"Connected to broker at {mqtt_broker}:{mqtt_port}")
        result, mid = client.subscribe(mqtt_topic)
        if result == mqtt.MQTT_ERR_SUCCESS:
            logging.debug(f"Subscribed to {mqtt_topic} successfully.")
        else:
            logging.error(f"Failed to subscribe to {mqtt_topic}, result code: {result}")
    else:
        logging.error(f"Failed to connect, reason code: {reason_code}")

def mqtt_loop(broker, port, user, password, topic):
    """Run the MQTT client loop."""
    client = mqtt.Client()

    client.on_message = on_message
    client.on_connect = on_connect

    client.enable_logger()

    if user and password:
        client.username_pw_set(user, password)

    logging.debug(f"Connecting to broker {broker}...")
    try:
        client.connect(broker, port, 60)
    except Exception as e:
        logging.error(f"Unable to connect to MQTT broker {broker}: {e}")
        return

    client.subscribe(topic)
    client.loop_forever()

def start_mqtt():
    """Start MQTT clients in separate threads."""
    threads = []

    if mqtt_broker:
        mosquitto_thread = Thread(target=mqtt_loop, args=(mqtt_broker, mqtt_port, mqtt_user, mqtt_password, mqtt_topic))
        mosquitto_thread.daemon = True
        threads.append(mosquitto_thread)

    if ttn_broker:
        ttn_thread = Thread(target=mqtt_loop, args=(ttn_broker, ttn_port, ttn_user, ttn_password, ttn_topic))
        ttn_thread.daemon = True
        threads.append(ttn_thread)

    for thread in threads:
        thread.start()

if __name__ != "__main__":
    logging.debug("Starting MQTT clients...")
    start_mqtt()

if __name__ == "__main__":
    logging.debug("Starting Flask app...")
    start_mqtt()
    app.run(host='0.0.0.0', port=5000)
