from flask import Flask, jsonify
import paho.mqtt.client as mqtt
import psycopg2
import os
import json
from urllib.parse import quote as url_quote 


app = Flask(__name__)

# 从环境变量获取配置
db_config = {
    'dbname': os.environ.get('DB_NAME'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'host': os.environ.get('DB_HOST')
}

mqtt_broker = os.environ.get('MQTT_BROKER')
mqtt_port = int(os.environ.get('MQTT_PORT'))
mqtt_user = os.environ.get('MQTT_USER')
mqtt_password = os.environ.get('MQTT_PASSWORD')
mqtt_topic = "v3/smart-bin-mqtt-server@ttn/devices/#"

def init_db():
    conn = psycopg2.connect(**db_config)
    return conn

def on_message(client, userdata, message):
    payload = json.loads(message.payload.decode())
    bin_id = payload.get('bin_id')
    fill_level = payload.get('fill_level_percentage')

    conn = init_db()
    cursor = conn.cursor()
    insert_query = """INSERT INTO smartbin.mockdata (bin_id, fill_level_percentage) VALUES (%s, %s)"""
    cursor.execute(insert_query, (bin_id, fill_level))
    conn.commit()
    cursor.close()
    conn.close()

def init_mqtt():
    client = mqtt.Client()
    client.username_pw_set(mqtt_user, mqtt_password)
    client.on_message = on_message
    client.connect(mqtt_broker, mqtt_port, 60)
    client.subscribe(mqtt_topic)
    client.loop_start()

@app.route('/get_bin_data', methods=['GET'])
def get_bin_data():
    conn = init_db()
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

if __name__ == "__main__":
    init_mqtt()
    app.run(host='0.0.0.0', port=5000)

