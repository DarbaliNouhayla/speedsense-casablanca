import json
import logging
from pydantic import BaseModel, Field, ValidationError
import paho.mqtt.client as mqtt
from speedsense_db_utils import insert_speed_reading

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TOPIC = "traffic/#"

# Payload Validation Schema
class TelemetryPayload(BaseModel):
    sensor_id: str = Field(..., min_length=1)
    seq: int = Field(..., ge=0)
    speed_kmh: float = Field(..., ge=0.0, le=250.0)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info(f"Connected to MQTT Broker on {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(TOPIC)
        logging.info(f"Subscribed to topic pattern: {TOPIC}")
    else:
        logging.error(f"Failed to connect to MQTT broker, return code: {rc}")

def on_message(client, userdata, msg):
    try:
        # 1. Parse JSON payload
        raw_payload = msg.payload.decode("utf-8")
        data = json.loads(raw_payload)

        # 2. Validate payload with Pydantic
        telemetry = TelemetryPayload(**data)

        # 3. Store in DB via helper function
        result = insert_speed_reading(
            sensor_id=telemetry.sensor_id,
            seq=telemetry.seq,
            speed_kmh=telemetry.speed_kmh,
            is_simulated=("sim" in telemetry.sensor_id or "esp" not in telemetry.sensor_id)
        )

        speeding_str = "⚠️ SPEEDING DETECTED" if result["is_speeding"] else "OK"
        logging.info(
            f"Saved seq={telemetry.seq} | Sensor={telemetry.sensor_id} | "
            f"Speed={telemetry.speed_kmh} km/h (Limit: {result['speed_limit']}) | {speeding_str}"
        )

    except json.JSONDecodeError:
        logging.warning(f"Rejected non-JSON payload on topic {msg.topic}: {msg.payload}")
    except ValidationError as ve:
        logging.warning(f"Validation failed for payload on topic {msg.topic}: {ve}")
    except Exception as e:
        logging.error(f"Error processing message: {e}")

def run_subscriber():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    logging.info("Starting MQTT Subscriber loop...")
    client.loop_forever()

if __name__ == "__main__":
    run_subscriber()
