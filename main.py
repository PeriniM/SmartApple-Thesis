import asyncio
from bleak import BleakClient, BleakScanner, BleakError
from decouple import config
from influxdb_client import InfluxDBClient, Point, WriteOptions
from datetime import datetime
import re

# Precompiled regular expression pattern
pattern = re.compile(r'(\d+),(-?\d+),G:([\d.-]+),([\d.-]+),([\d.-]+),A:([\d.-]+),([\d.-]+),([\d.-]+),Q:([\d.-]+),([\d.-]+),([\d.-]+),([\d.-]+)')

# 0 means stop notification, 1 means start notification
PROGRAM_COMMAND_UUID = "19b10000-8002-537e-4f6c-d104768a1214" 
SENSORS_UUID = "19b10000-A001-537e-4f6c-d104768a1214" # UUID to read from

nicla_address = "EE:DF:46:E7:08:80" # Nicla Sense Me device address
device_name = None
client = None
isStarted = False
push2influxdb = False

if push2influxdb:
    # InfluxDB Settings
    INFLUXDB_URL = config('INFLUXDB_URL', cast=str)
    INFLUXDB_TOKEN = config('INFLUXDB_TOKEN', cast=str)
    INFLUXDB_ORG = config('INFLUXDB_ORG', cast=str)
    INFLUXDB_BUCKET = config('INFLUXDB_BUCKET', cast=str)

    # Setup InfluxDB client
    client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, debug=True, org=INFLUXDB_ORG)

    # Configure batch write client
    write_api = client.write_api(write_options=WriteOptions(
            batch_size=100,
            flush_interval=10_000,
            jitter_interval=2_000,
            retry_interval=5_000,
            max_retries=5,
            max_retry_delay=30_000,
            max_close_wait=300_000,
            exponential_base=2
        ))

# Helper function to write to InfluxDB directly without appending
def write_to_influxdb(measurement, data, timestamp):
    point = Point(measurement).time(timestamp)
    for key, value in data.items():
        point = point.field(key, value)
    write_api.write(INFLUXDB_BUCKET, INFLUXDB_ORG, point)

def notification_handler(sender: int, data: bytearray):
    global pattern

    raw_data = data.decode('utf-8')
    match = pattern.match(raw_data)
    if match:
        packet_id, rssi, g_x, g_y, g_z, a_x, a_y, a_z, q_x, q_y, q_z, q_w = match.groups()
        timestamp = datetime.utcnow()
        if push2influxdb:
            write_to_influxdb("movement_sensor_data", {
                "packet_id": int(packet_id),
                "gyro_x": float(g_x),
                "gyro_y": float(g_y),
                "gyro_z": float(g_z),
                "accel_x": float(a_x),
                "accel_y": float(a_y),
                "accel_z": float(a_z),
                "quat_x": float(q_x),
                "quat_y": float(q_y),
                "quat_z": float(q_z),
                "quat_w": float(q_w)
            }, timestamp)
        
        print(f"Packet ID: {packet_id}")
        print(f"RSSI: {rssi}")
        print(f"Gyroscope: [{g_x}, {g_y}, {g_z}]")
        print(f"Accelerometer: [{a_x}, {a_y}, {a_z}]")
        print(f"Quaternion: [{q_x}, {q_y}, {q_z}, {q_w}]")
    else:
        print("Invalid data received:", raw_data)

async def main_loop(address):
    global isStarted, client
    while True:
        try:
            async with BleakClient(address) as client:
                print("Connected successfully!")
                if not isStarted:
                    # send a byte 1 to start the program to the command characteristic
                    await client.write_gatt_char(PROGRAM_COMMAND_UUID, bytearray([1]))
                    await client.start_notify(SENSORS_UUID, notification_handler)
                    isStarted = True

                while client.is_connected:
                    await asyncio.sleep(1)

        except BleakError as e:
            print(f"BleakError while connecting: {e}")
        except Exception as e:
            print(f"Unexpected error while connecting: {e}")
        finally:
            print("Disconnected. Trying to reconnect...")
            isStarted = False
            await asyncio.sleep(0.5)
       
async def main():
    global nicla_address, client
    try:
        await main_loop(nicla_address)

    except Exception as e:
        print(f"Unexpected error: {e}")
    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        print("Cleaning up...")
        if client:
            try:
                if client.is_connected:
                    await client.disconnect()
            except Exception as e:
                print(f"Error during cleanup: {e}")

loop = asyncio.get_event_loop()

try:
    loop.run_until_complete(main())
finally:
    loop.close()