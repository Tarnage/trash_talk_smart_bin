#!/bin/bash

pass='YOUR TTN API KEY' # Get this key from the TTN console: Integrations -> MQTT -> Generate new API Key
user='USERNAME' # Get this username from the TTN console: Integrations -> MQTT -> Username
host='au1.cloud.thethings.network'
port='1883'
topic='v3/<USERNAME>/devices/smart-bin-dev/down/push' # Replace <USERNAME> same as user

# this payload is too big
#payload='{"bin_id": "6969", "fill_level_percentage": "0.5", "temperature_celsius": "25", "latitude": "1.0", "longitude": "1.0", "collection_frequency_per_month": "1", "average_collection_time_days": "1", "tilt_status": "Tilted",  "displacement": "Not Displaced", "days_since_last_emptied": "69", "communication_status": "Connected", "battery_level_percentage": "69"}'

# payload='{"bin_id": "6969","temperature_celsius": "25"}'


payload='{"bin_id": "6969","fill_level_percentage": "0.5"}'
payload_base64=$(echo -n $payload | base64)

message='{"downlinks":[{"frm_payload":"'$payload_base64'", "f_port": 15, "priority": "NORMAL"}]}'

mosquitto_pub -h $host -t $topic -m "$message" -u $user -P $pass -d
