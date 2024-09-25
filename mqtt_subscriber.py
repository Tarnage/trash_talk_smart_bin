import paho.mqtt.client as mqtt
import os
import json
import base64
from app import app, db, SmartBinData

# MQTT configuration from environment variables
mqtt_broker = os.environ.get('MQTT_BROKER')
mqtt_port = int(os.environ.get('MQTT_PORT'))
mqtt_user = os.environ.get('MQTT_USER')
mqtt_password = os.environ.get('MQTT_PASSWORD')
mqtt_topic = os.environ.get('MQTT_TOPIC')

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
        return json.loads(decoded_bytes)
    except Exception as e:
        print(f"Error decoding payload: {e}")
        return None

def on_message(client, userdata, message):
    payload = decode_payload(message.payload)
    if not payload:
        return

    with app.app_context():
        bin_id = payload.get('bin_id')
        if not bin_id:
            print("Missing bin_id in payload.")
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
        print("Data inserted/updated successfully.")

def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print(f"Connected to broker and subscribed to {mqtt_topic}")
        client.subscribe(mqtt_topic)

def init_mqtt():
    client = mqtt.Client()

    client.on_message = on_message
    client.on_connect = on_connect

    if mqtt_user and mqtt_password:
        client.username_pw_set(mqtt_user, mqtt_password)

    client.connect(mqtt_broker, mqtt_port, 60)
    client.loop_start()

if __name__ == "__main__":
    init_mqtt()
