from flask import Flask, jsonify, request
import paho.mqtt.client as mqtt
import psycopg2
import os
import json

app = Flask(__name__)

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


# MQTT callback functions
def get_db_connection():
    """Create and return a new database connection."""
    try:
        conn = psycopg2.connect(**db_config)
        return conn
    except psycopg2.DatabaseError as e:
        app.logger.error(f"Database connection error: {e}")
        return None

def on_message(client, userdata, message):
    # handle message from MQTT server
    payload = json.loads(message.payload.decode())

    # insert data into database
    bin_id = payload.get('bin_id')
    latitude = payload.get('latitude')
    longitude = payload.get('longitude')
    collection_frequency_per_month = payload.get('collection_frequency_per_month')
    average_collection_time_days = payload.get('average_collection_time_days')
    tilt_status = payload.get('tilt_status')
    fill_level_percentage = payload.get('fill_level_percentage')
    temperature_celsius = payload.get('temperature_celsius')
    displacement = payload.get('displacement')
    days_since_last_emptied = payload.get('days_since_last_emptied')
    communication_status = payload.get('communication_status')
    battery_level_percentage = payload.get('battery_level_percentage')


    conn = init_db()
    cursor = conn.cursor()

    # insert into database
    insert_query = """
    INSERT INTO smartbin.mockdata (
        bin_id, latitude, longitude, collection_frequency_per_month, 
        average_collection_time_days, tilt_status, fill_level_percentage, 
        temperature_celsius, displacement, days_since_last_emptied, 
        communication_status, battery_level_percentage
    ) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    cursor.execute(insert_query, (
        bin_id, latitude, longitude, collection_frequency_per_month, 
        average_collection_time_days, tilt_status, fill_level_percentage, 
        temperature_celsius, displacement, days_since_last_emptied, 
        communication_status, battery_level_percentage
    ))

    conn.commit()
    cursor.close()
    conn.close()

#
# def init_mqtt():
#   """Initialize and start the MQTT client."""
#   client = mqtt.Client()
#   client.username_pw_set(mqtt_user, mqtt_password)
#   client.connect(mqtt_broker, mqtt_port, 60)
#   client.subscribe(mqtt_topic)
#   client.loop_start()


def init_mqtt():
    client = mqtt.Client()
    if mqtt_user and mqtt_password:
        client.username_pw_set(mqtt_user, mqtt_password)

    client.on_message = on_message
    client.connect(mqtt_broker, mqtt_port, 60)
    client.subscribe(mqtt_topic)
    client.loop_start()


@app.route('/')
def home():
    """Home route."""
    return "Welcome to the Flask MQTT Application!"

@app.route('/get_bin_data', methods=['GET'])
def get_bin_data():
    """Retrieve and return all bin data from the database."""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM smartbin.mockdata")
        result = cursor.fetchall()
        cursor.close()
        conn.close()

        data = []
        for row in result:
            data.append({
                'bin_id': row[0],
                'latitude': row[1],
                'longitude': row[2],
                'collection_frequency_per_month': row[3],
                'average_collection_time_days': row[4],
                'tilt_status': row[5],
                'fill_level_percentage': row[6],
                'temperature_celsius': row[7],
                'displacement': row[8],
                'days_since_last_emptied': row[9],
                'communication_status': row[10],
                'battery_level_percentage': row[11]
            })
        return jsonify(data)
    else:
        return jsonify({"error": "Database connection error"}), 500

@app.route('/post_bin_data', methods=['POST'])
def post_bin_data():
    """Receive data from HTTP POST requests and store it in the database."""
    try:
        data = request.get_json()  # Get JSON data from POST request
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Extract all relevant fields
        bin_id = data.get('bin_id')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        collection_frequency_per_month = data.get('collection_frequency_per_month')
        average_collection_time_days = data.get('average_collection_time_days')
        tilt_status = data.get('tilt_status')
        fill_level_percentage = data.get('fill_level_percentage')
        temperature_celsius = data.get('temperature_celsius')
        displacement = data.get('displacement')
        days_since_last_emptied = data.get('days_since_last_emptied')
        communication_status = data.get('communication_status')
        battery_level_percentage = data.get('battery_level_percentage')

        if bin_id is None or fill_level_percentage is None:
            return jsonify({"error": "Invalid data"}), 400

        # Insert data into the database
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            insert_query = """
            INSERT INTO smartbin.mockdata (
                bin_id, latitude, longitude, 
                collection_frequency_per_month, average_collection_time_days, 
                tilt_status, fill_level_percentage, 
                temperature_celsius, displacement, 
                days_since_last_emptied, communication_status, 
                battery_level_percentage
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                bin_id, latitude, longitude, 
                collection_frequency_per_month, average_collection_time_days, 
                tilt_status, fill_level_percentage, 
                temperature_celsius, displacement, 
                days_since_last_emptied, communication_status, 
                battery_level_percentage
            ))
            conn.commit()  # Commit the transaction
            cursor.close()  # Close the cursor
            conn.close()    # Close the connection
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"error": "Database connection error"}), 500
    except Exception as e:
        app.logger.error(f"Error processing POST request: {e}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    init_mqtt()
    app.run(host='0.0.0.0', port=5000, debug=True)

