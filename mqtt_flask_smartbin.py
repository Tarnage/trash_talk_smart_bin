from flask import Flask
import paho.mqtt.client as mqtt
import psycopg2
import os
import json
import base64

app = Flask(__name__)

app.logger.setLevel('INFO')

# Database configuration from environment variables
db_config = {
    'dbname': os.environ.get('DB_NAME'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'host': os.environ.get('DB_HOST')
}

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


def get_db_connection():
    try:
        conn = psycopg2.connect(**db_config)
        return conn
    except psycopg2.DatabaseError as e:
        app.logger.error(f"Database connection error: {e}")
        return None
    

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


def create_smartbin_table():
    """Create the table if it does not exist."""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS smartbin.mockdata
        (
            bin_id character varying(10) COLLATE pg_catalog."default" NOT NULL,
            latitude numeric(12,8),
            longitude numeric(12,8),
            collection_frequency_per_month integer,
            average_collection_time_days integer,
            tilt_status character varying(20) COLLATE pg_catalog."default",
            fill_level_percentage numeric(5,2),
            temperature_celsius numeric(5,2),
            displacement character varying(20) COLLATE pg_catalog."default",
            days_since_last_emptied integer,
            communication_status character varying(20) COLLATE pg_catalog."default",
            battery_level_percentage numeric(4,2),
            CONSTRAINT mockdata_pkey PRIMARY KEY (bin_id)
        )

        TABLESPACE pg_default;

        ALTER TABLE IF EXISTS smartbin.mockdata
        OWNER to "Dean";
        """)

        conn.commit()
        cursor.close()
        conn.close()
    else:
        app.logger.error("Failed to connect to the database.")


def on_message(client, userdata, message):
    try:
        payload = decode_payload(message.payload)

        if not payload:
            return

        conn = get_db_connection()

        if conn:
            cursor = conn.cursor()
            
            # Dynamically construct the SQL query based on the payload
            # We may have to break payloads up to smaller chunks to be able to send it up to TTN
            columns = []
            values = []
            updates = []

            for prop in PROPERTIES:
                if prop in payload:
                    columns.append(prop)
                    values.append("'{}'".format(payload[prop]))
                    if prop not in EXCLUDED_PROPERTIES:
                        updates.append("{} = excluded.{}".format(prop, prop))

            if columns and values:
                sql = """
                    INSERT INTO smartbin.mockdata({})
                    VALUES ({})
                    ON CONFLICT (bin_id) DO UPDATE
                    SET {};
                    """.format(
                        ', '.join(columns),
                        ', '.join(values),
                        ', '.join(updates)
                    )

            cursor.execute(sql)

            conn.commit()
            cursor.close()
            conn.close()

            app.logger.info("Data inserted successfully.")
        else:
            app.logger.error("Failed to connect to the database.")
    except Exception as e:
        app.logger.error(f"Error processing message: {e}")


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        app.logger.warning(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
    else:
        # we should always subscribe from on_connect callback to be sure
        # our subscribed is persisted across reconnections.
        app.logger.info(f"Subscibed to {mqtt_topic}")
        client.subscribe(mqtt_topic)


def on_subscribe(client, userdata, mid, reason_code_list, properties):
    # Since we subscribed only for a single channel, reason_code_list contains
    # a single entry
    if reason_code_list[0].is_failure:
        app.logger.warning(f"Broker rejected you subscription: {reason_code_list[0]}")
    else:
        app.logger.info(f"Broker granted the following QoS: {reason_code_list[0].value}")


def init_mqtt():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    # set callbacks
    client.on_message = on_message
    client.on_connect = on_connect
    client.on_subscribe = on_subscribe

    # set password and username
    if mqtt_user and mqtt_password:
        client.username_pw_set(mqtt_user, mqtt_password)
    client.user_data_set([])
    client.connect(mqtt_broker, mqtt_port, 60)
    client.loop_start()


# We dpn't need these routes, we dont want random people spamming the database

# @app.route('/')
# def home():
#     """Home route."""
#     return "Welcome to the Flask MQTT Application!"

# @app.route('/get_bin_data', methods=['GET'])
# def get_bin_data():
#     """Retrieve and return all bin data from the database."""
#     conn = get_db_connection()
#     if conn:
#         cursor = conn.cursor()
#         cursor.execute("SELECT * FROM smartbin.mockdata")
#         result = cursor.fetchall()
#         cursor.close()
#         conn.close()

#         data = []
#         for row in result:
#             data.append({
#                 'bin_id': row[0],
#                 'latitude': row[1],
#                 'longitude': row[2],
#                 'collection_frequency_per_month': row[3],
#                 'average_collection_time_days': row[4],
#                 'tilt_status': row[5],
#                 'fill_level_percentage': row[6],
#                 'temperature_celsius': row[7],
#                 'displacement': row[8],
#                 'days_since_last_emptied': row[9],
#                 'communication_status': row[10],
#                 'battery_level_percentage': row[11]
#             })
#         return jsonify(data)
#     else:
#         return jsonify({"error": "Database connection error"}), 500

# @app.route('/post_bin_data', methods=['POST'])
# def post_bin_data():
#     """Receive data from HTTP POST requests and store it in the database."""
#     try:
#         data = request.get_json()  # Get JSON data from POST request
#         if not data:
#             return jsonify({"error": "No data provided"}), 400

#         # Extract all relevant fields
#         bin_id = data.get('bin_id')
#         latitude = data.get('latitude')
#         longitude = data.get('longitude')
#         collection_frequency_per_month = data.get('collection_frequency_per_month')
#         average_collection_time_days = data.get('average_collection_time_days')
#         tilt_status = data.get('tilt_status')
#         fill_level_percentage = data.get('fill_level_percentage')
#         temperature_celsius = data.get('temperature_celsius')
#         displacement = data.get('displacement')
#         days_since_last_emptied = data.get('days_since_last_emptied')
#         communication_status = data.get('communication_status')
#         battery_level_percentage = data.get('battery_level_percentage')

#         if bin_id is None or fill_level_percentage is None:
#             return jsonify({"error": "Invalid data"}), 400

#         # Insert data into the database
#         conn = get_db_connection()
#         if conn:
#             cursor = conn.cursor()
#             insert_query = """
#             INSERT INTO smartbin.mockdata (
#                 bin_id, latitude, longitude, 
#                 collection_frequency_per_month, average_collection_time_days, 
#                 tilt_status, fill_level_percentage, 
#                 temperature_celsius, displacement, 
#                 days_since_last_emptied, communication_status, 
#                 battery_level_percentage
#             ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#             """
#             cursor.execute(insert_query, (
#                 bin_id, latitude, longitude, 
#                 collection_frequency_per_month, average_collection_time_days, 
#                 tilt_status, fill_level_percentage, 
#                 temperature_celsius, displacement, 
#                 days_since_last_emptied, communication_status, 
#                 battery_level_percentage
#             ))
#             conn.commit()
#             cursor.close()
#             conn.close()
#             return jsonify({"status": "success"}), 200
#         else:
#             return jsonify({"error": "Database connection error"}), 500
#     except Exception as e:
#         app.logger.error(f"Error processing POST request: {e}")
#         return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    init_mqtt()
    create_smartbin_table() # Create the table if it does not exist
    app.run(host='0.0.0.0', port=6969, debug=True)

