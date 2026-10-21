#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "secrets.h"

// MQTT Broker settings
const char* mqtt_server = MQTT_BROKER_IP;
const int mqtt_port = 1883;
const char* mqtt_topic = "traffic/sensor_esp_01";

WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastMsg = 0;
int seq = 0;

void setup_wifi() {
    delay(10);
    Serial.println();
    Serial.print("Connecting to ");
    Serial.println(WIFI_SSID);

    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

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
        // Attempt to connect with client ID "ESP8266Client"
        if (client.connect("ESP8266Client")) {
            Serial.println("connected");
        } else {
            Serial.print("failed, rc=");
            Serial.print(client.state());
            Serial.println(" try again in 5 seconds");
            delay(5000);
        }
    }
}

void setup() {
    Serial.begin(115200);
    setup_wifi();
    client.setServer(mqtt_server, mqtt_port);
}

void loop() {
    if (!client.connected()) {
        reconnect();
    }
    client.loop();

    unsigned long now = millis();
    if (now - lastMsg > 2000) {
        lastMsg = now;
        seq++;

        // Generate simulated speed data for testing until HB100 arrives
        float speed_kmh = random(30, 85) + (random(0, 99) / 100.0);

        // Create JSON payload
        JsonDocument doc;
        doc["sensor_id"] = "esp8266_node_01";
        doc["seq"] = seq;
        doc["speed_kmh"] = speed_kmh;

        char jsonBuffer[256];
        serializeJson(doc, jsonBuffer);

        client.publish(mqtt_topic, jsonBuffer);
        Serial.print("Published message: ");
        Serial.println(jsonBuffer);
    }
}
