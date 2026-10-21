import json
import random
import time
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883
TOPIC = "traffic/sensor_sim_01"

client = mqtt.Client()
client.connect(BROKER, PORT, 60)

seq = 0
print("Starting simulated sensor publisher...")
try:
    while True:
        seq += 1
        # Generate realistic Casablanca urban speeds (mean 55 km/h, sd 12)
        speed = max(20.0, min(120.0, random.gauss(55, 12)))
        payload = {
            "sensor_id": "sensor_sim_01",
            "seq": seq,
            "speed_kmh": round(speed, 2),
        }
        client.publish(TOPIC, json.dumps(payload))
        print(f"Published: {payload}")
        time.sleep(2)
except KeyboardInterrupt:
    print("Stopped simulation.")
    client.disconnect()
