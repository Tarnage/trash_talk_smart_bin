from flask import Flask
import paho.mqtt.client as mqtt
import os
import json
import base64
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import VARCHAR, NUMERIC, INTEGER

app = Flask(__name__)

# Database configuration from environment variables
db_user = os.environ.get('DB_USER')
db_password = os.environ.get('DB_PASSWORD')
db_host = os.environ.get('DB_HOST')
db_name = os.environ.get('DB_NAME')
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# MQTT configuration from environment variables
mqtt_broker = os.environ.get('MQTT_BROKER')
mqtt_port = int(os.environ.get('MQTT_PORT'))
mqtt_user = os.environ.get('MQTT_USER')
mqtt_password = os.environ.get('MQTT_PASSWORD')
mqtt_topic = os.environ.get('MQTT_TOPIC')

# Properties to be stored in the database
PROPERTIES = [
    "bin_id", 
    "latitude", 
    "longitude", 
    "collection_frequency_per_month", 
    "average_collection_time_days", 
    "tilt_status",
    "fill_level_percentage",
    "temperature_celsius", 
    "displacement", 
    "days_since_last_emptied",
    "communication_status", 
    "battery_level_percentage"
]

# Properties to be excluded from the update query
EXCLUDED_PROPERTIES = ["bin_id"]

class SmartBinData(db.Model):
    __tablename__ = 'mockdata'
    bin_id = db.Column(VARCHAR(10), primary_key=True, nullable=False)
    latitude = db.Column(NUMERIC(12, 8))
    longitude = db.Column(NUMERIC(12, 8))
    collection_frequency_per_month = db.Column(INTEGER)
    average_collection_time_days = db.Column(INTEGER)
    tilt_status = db.Column(VARCHAR(20))
    fill_level_percentage = db.Column(NUMERIC(5, 2))
    temperature_celsius = db.Column(NUMERIC(5, 2))
    displacement = db.Column(VARCHAR(20))
    days_since_last_emptied = db.Column(INTEGER)
    communication_status = db.Column(VARCHAR(20))
    battery_level_percentage = db.Column(NUMERIC(4, 2))


def decode_payload(payload):
    """Decode the payload and return a dictionary."""
    try:
        message = json.loads(payload)
        decoded_bytes = base64.b64decode(message['downlink_queued']['frm_payload']).decode('utf-8')
        decoded_payload = json.loads(decoded_bytes)

        app.logger.info(f"Decoded payload: {decoded_payload}")

        return decoded_payload

    except json.JSONDecodeError as e:
        app.logger.error(f"Error decoding payload: {e}")
        return None


def on_message(client, userdata, message):
    try:
        payload = decode_payload(message.payload)

        if not payload:
            return

        columns = []
        values = {}
        updates = {}

        for prop in PROPERTIES:
            if prop in payload:
                columns.append(prop)
                values[prop] = payload[prop]
                if prop not in EXCLUDED_PROPERTIES:
                    updates[prop] = payload[prop]

        if columns:
            bin_id = values.get("bin_id")

            if bin_id:
                existing_bin = SmartBinData.query.filter_by(bin_id=bin_id).first()

                if existing_bin:
                    # Update existing record
                    for key, value in updates.items():
                        setattr(existing_bin, key, value)
                else:
                    # Insert new record
                    new_bin = SmartBinData(**values)
                    db.session.add(new_bin)

                db.session.commit()

                app.logger.info("Data inserted/updated successfully.")
            else:
                app.logger.error("Missing bin_id in payload.")
    except Exception as e:
        app.logger.error(f"Error processing message: {e}")


def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code != 0:
        app.logger.warning(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
    else:
        app.logger.info(f"Connected to broker and subscribed to {mqtt_topic}")
        client.subscribe(mqtt_topic)



def on_subscribe(client, userdata, mid, reason_code_list, properties):
    if reason_code_list[0].is_failure:
        app.logger.warning(f"Broker rejected your subscription: {reason_code_list[0]}")
    else:
        app.logger.info(f"Broker granted the following QoS: {reason_code_list[0].value}")


def init_mqtt():
    client = mqtt.Client()

    # Set callbacks
    client.on_message = on_message
    client.on_connect = on_connect
    client.on_subscribe = on_subscribe

    # Set password and username
    if mqtt_user and mqtt_password:
        client.username_pw_set(mqtt_user, mqtt_password)
    client.user_data_set([])
    client.connect(mqtt_broker, mqtt_port, 60)
    client.loop_start()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create tables if not exist
    init_mqtt()
    app.run(host='0.0.0.0', port=6969, debug=True)
