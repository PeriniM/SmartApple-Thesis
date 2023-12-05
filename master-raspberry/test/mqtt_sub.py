import sys
from influxdb_client import InfluxDBClient, Point, WriteOptions
import paho.mqtt.client as paho
from datetime import datetime
from decouple import config

nicla_address = ["EE:DF:46:E7:08:80", "9C:E3:E6:C9:4A:C8"]
send2influxdb = True
prod_line_id = ["test", "test"]

if send2influxdb:
    # InfluxDB Settings
    INFLUXDB_URL = config('INFLUXDB_URL', cast=str)
    INFLUXDB_TOKEN = config('INFLUXDB_TOKEN', cast=str)
    INFLUXDB_ORG = config('INFLUXDB_ORG', cast=str)
    INFLUXDB_BUCKET = config('INFLUXDB_BUCKET', cast=str)

    # Setup InfluxDB client
    influxdb_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, debug=True, org=INFLUXDB_ORG)

    # Configure batch write client
    write_api = influxdb_client.write_api(write_options=WriteOptions(
            batch_size=50,
            flush_interval=10_000,
            jitter_interval=2_000,
            retry_interval=5_000,
            max_retries=5,
            max_retry_delay=30_000,
            max_close_wait=300_000,
            exponential_base=2
        ))

# Helper function to write to InfluxDB directly without appending
def write_to_influxdb(address, prod_line_id, data, timestamp):
    measurement = "nicla"
    tags = {
        "address": address,
        "production_line": prod_line_id,
    }

    point = Point(measurement).time(timestamp)
    for key, value in tags.items():
        point = point.tag(key, value)
    for key, value in data.items():
        point = point.field(key, value)

    write_api.write(INFLUXDB_BUCKET, INFLUXDB_ORG, point)

def message_handling(client, userdata, msg):
    # print(f"{msg.topic}: {msg.payload.decode()}")
    data = msg.payload.decode().split(",")
    curr_addr_idx = nicla_address.index(msg.topic.split("/")[1])
    if "prod_line" in msg.topic:
        # Extract the production line string from the message
        prod_line_id[curr_addr_idx] = data[0]
    elif "movement_sensor_data" in msg.topic:
        # measurement = f"nicla.{nicla_address[curr_addr_idx]}.movement_sensor_data.{prod_line_id[curr_addr_idx]}"
        timestamp = datetime.strptime(data[0], "%Y-%m-%d %H:%M:%S.%f")

        # Extract the data values from the message
        fields = {
            "packet_id": int(data[1]),
            "g_x": float(data[2]),
            "g_y": float(data[3]),
            "g_z": float(data[4]),
            "a_x": float(data[5]),
            "a_y": float(data[6]),
            "a_z": float(data[7]),
            "q_x": float(data[8]),
            "q_y": float(data[9]),
            "q_z": float(data[10]),
            "q_w": float(data[11]),
        }

        # print(f"{measurement}: {fields}: {timestamp}")
        if send2influxdb:
            # Write to InfluxDB
            write_to_influxdb(nicla_address[curr_addr_idx], prod_line_id[curr_addr_idx], fields, timestamp)

client = paho.Client()
client.on_message = message_handling
if client.connect("localhost", 1883, 60) != 0:
    print("Couldn't connect to the mqtt broker")
    sys.exit(1)

for address in nicla_address:
    client.subscribe(f"nicla/{address}/movement_sensor_data", 0)
    client.subscribe(f"nicla/{address}/prod_line", 0)

try:
    print("Press CTRL+C to exit...")
    client.loop_forever()
except Exception:
    print("Caught an Exception, something went wrong...")
finally:
    print("Disconnecting from the MQTT broker")
    client.disconnect()