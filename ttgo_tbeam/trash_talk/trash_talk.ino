#include <WiFi.h>
#include <PubSubClient.h>
#include <Base64.h> 
#include <TinyGPS++.h>
#include <axp20x.h>
#include <Wire.h>
#include "DFRobot_MLX90614.h"


const int trigPin = 32; 
const int echoPin = 33; 
const float soundSpeed = 0.0343;
const int bin_size = 100; 
const int tiltPin = 35; 

// WiFi and MQTT Broker details
const char* ssid = "";   
const char* password = "";  
const char* mqtt_server = "";  
const int mqtt_port = 1883;
const char* mqtt_topic = "";

TinyGPSPlus gps;
HardwareSerial GPS(1);  
AXP20X_Class axp;

#define MLX90614_I2C_ADDR 0x5A   
DFRobot_MLX90614_I2C sensor(MLX90614_I2C_ADDR, &Wire);  

WiFiClient espClient;
PubSubClient client(espClient);
long lastMsg = 0;
char msg[100];

void setup() {
  
  Serial.begin(115200);
  
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);


  pinMode(tiltPin, INPUT);
  
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);  

  setup_gps();
  
  while (NO_ERR != sensor.begin()) {
    Serial.println("Communication with device failed, please check connection");
    delay(3000);
  }
  Serial.println("Begin ok!");

  sensor.setEmissivityCorrectionCoefficient(1.0);
  sensor.setI2CAddress(0x5A);
  sensor.setMeasuredParameters(sensor.eIIR100, sensor.eFIR1024);

  sensor.enterSleepMode();
  delay(50);
  sensor.enterSleepMode(false);
  delay(200);
}

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());  
}

void reconnect() {
  
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("T-BEAM_Client")) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);  
    }
  }
}

void setup_gps() {
  Wire.begin(21, 22);  
  if (!axp.begin(Wire, AXP192_SLAVE_ADDRESS)) {
    Serial.println("AXP192 Begin PASS");
  } else {
    Serial.println("AXP192 Begin FAIL");
  }

  axp.setPowerOutPut(AXP192_LDO2, AXP202_ON);
  axp.setPowerOutPut(AXP192_LDO3, AXP202_ON);
  axp.setPowerOutPut(AXP192_DCDC2, AXP202_ON);
  axp.setPowerOutPut(AXP192_EXTEN, AXP202_ON);
  axp.setPowerOutPut(AXP192_DCDC1, AXP202_ON);

  GPS.begin(9600, SERIAL_8N1, 34, 12);  
}

float getDistance() {
  digitalWrite(trigPin, LOW);  
  delayMicroseconds(2);  

  digitalWrite(trigPin, HIGH);  
  delayMicroseconds(10);  
  digitalWrite(trigPin, LOW);  

  long duration = pulseIn(echoPin, HIGH);  

  float distance = (duration * soundSpeed) / 2;
  float fill = (distance / bin_size) * 100;

  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.println(" cm");
  Serial.print("Fill Percentage: ");
  Serial.println(fill);

  return fill;
}

void pub_msg() {
  Serial.print("Publishing message: ");
  Serial.println(msg);  
  client.publish(mqtt_topic, msg);  
}

void send_fill() {
  float distance = getDistance();
  snprintf(msg, 100, "{\"bin_id\":\"6969\",\"fill_level_percentage\":\"%.2f\"}", distance);
  pub_msg();
}

float getTemp() {
  return sensor.getObjectTempCelsius();  
}

void send_temp() {
  float temp = getTemp();
  snprintf(msg, 100, "{\"bin_id\":\"6969\",\"temperature_celsius\":\"%.2f\"}", temp);
  pub_msg();
}

void send_gps() {
  float latitude;
  float longitude;

  if (gps.location.isValid()) {
    latitude = gps.location.lat();
    longitude = gps.location.lng();
  } else {
    
    latitude = 0.0;
    longitude = 0.0;
  }

  snprintf(msg, 100, "{\"bin_id\":\"6969\",\"latitude\": \"%.5f\", \"longitude\": \"%.5f\"}", latitude, longitude);
  pub_msg();
}

void send_tilt() {
  int tiltState = digitalRead(tiltPin);
  const char* tilted = (tiltState == HIGH) ? "tilted" : "not tilted";
  snprintf(msg, 100, "{\"bin_id\":\"6969\",\"tilt_status\":\"%s\"}", tilted);
  pub_msg();
}

void loop() {
  
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  
  while (GPS.available()) {
    gps.encode(GPS.read());
  }

  
  long now = millis();
  if (now - lastMsg > 30000) {  
    lastMsg = now;
    send_fill();  
    send_temp();  
    send_gps();    
    send_tilt();  
  }
}