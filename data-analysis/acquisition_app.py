import asyncio
from bleak import BleakClient, BleakScanner
from decouple import config
import paho.mqtt.client as paho
from datetime import datetime
import re
import os
import pandas as pd
from datetime import datetime

curr_dir = os.path.dirname(os.path.abspath(__file__))
save_dir = os.path.join(curr_dir, 'acquisitions')

# Precompiled regular expression pattern
pattern = re.compile(r'(\d+),G:([\d.-]+),([\d.-]+),([\d.-]+),A:([\d.-]+),([\d.-]+),([\d.-]+),Q:([\d.-]+),([\d.-]+),([\d.-]+),([\d.-]+)')

# 0 means stop notification, 1 means start notification
PROGRAM_COMMAND_UUID = "19b10000-8002-537e-4f6c-d104768a1214" 
SENSORS_UUID = "19b10000-A001-537e-4f6c-d104768a1214" # UUID to read from

nicla_address = ["EE:DF:46:E7:08:80", "9C:E3:E6:C9:4A:C8"]
connected_address = None
device_name = None
ble_client = None
mqtt_client = None
isStarted = False
send2mqtt = False
save2local = True
file_name = None
file_path = None
df = None
file_name = f"impacts_{datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
file_path = os.path.join(save_dir, file_name)
df = pd.DataFrame(columns=['_time', 'packet_id', 'gyro_x', 'gyro_y', 'gyro_z', 'accel_x', 'accel_y', 'accel_z', 'quat_x', 'quat_y', 'quat_z', 'quat_w'])
df.to_csv(file_path, header=True, index=False)

if send2mqtt:
    # MQTT Settings
    MQTT_ID = config('MQTT_ID', cast=str)
    MQTT_HOST = config('MQTT_HOST', cast=str)
    MQTT_PORT = config('MQTT_PORT', cast=int)

    # Setup MQTT client
    mqtt_client = paho.Client(client_id=MQTT_ID, clean_session=True, userdata=None, protocol=paho.MQTTv311, transport="tcp")

    if mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60) != 0:
        print("Couldn't connect to the mqtt broker")
    else:
        print("Connected to the mqtt broker")

# send through MQTT
def send_to_mqtt(topic, data):
    global mqtt_client
    mqtt_client.publish(topic, data, 0)

def notification_handler(sender: int, data: bytearray):
    global pattern, connected_address, send2mqtt, save2local, file_path, df

    raw_data = data.decode('utf-8')
    match = pattern.match(raw_data)
    if match:
        packet_id, g_x, g_y, g_z, a_x, a_y, a_z, q_x, q_y, q_z, q_w = match.groups()
        timestamp = datetime.utcnow()
        print(f"{timestamp},{packet_id},{g_x},{g_y},{g_z},{a_x},{a_y},{a_z},{q_x},{q_y},{q_z},{q_w}")

        if save2local:
            df.loc[len(df)] = [timestamp, packet_id, g_x, g_y, g_z, a_x, a_y, a_z, q_x, q_y, q_z, q_w]
            if int(packet_id) % 100 == 0:
                df.to_csv(file_path, header=False, index=False, mode='a')
                df = pd.DataFrame(columns=['_time', 'packet_id', 'gyro_x', 'gyro_y', 'gyro_z', 'accel_x', 'accel_y', 'accel_z', 'quat_x', 'quat_y', 'quat_z', 'quat_w'])
      
        if send2mqtt:
            # print(f"nicla/{connected_address}/movement_sensor_data", f"{timestamp},{packet_id},{g_x},{g_y},{g_z},{a_x},{a_y},{a_z},{q_x},{q_y},{q_z},{q_w}")
            send_to_mqtt(f"nicla/{connected_address}/movement_sensor_data", f"{timestamp},{packet_id},{g_x},{g_y},{g_z},{a_x},{a_y},{a_z},{q_x},{q_y},{q_z},{q_w}")
    else:
        print("Invalid data received:", raw_data)

async def main_loop(address):
    global isStarted, ble_client, connected_address
    isStarted = False
    
    while True:
        async with BleakClient(address, timeout=10.0) as ble_client:
            print("Connected successfully!")
            if not isStarted:
                # send a byte 1 to start the program to the command characteristic
                await ble_client.write_gatt_char(PROGRAM_COMMAND_UUID, bytearray([1]))
                await ble_client.start_notify(SENSORS_UUID, notification_handler)
                isStarted = True

            while ble_client.is_connected:
                await asyncio.sleep(0.1)
            
            # exit the loop if client is disconnected
            print("Disconnected from device.")
            connected_address = None
            break
       
async def main():
    global nicla_address, connected_address, ble_client, isStarted
    while True:
        try:
            # if client is not connected, scan for devices
            if not ble_client or not ble_client.is_connected:
                connected_address = None
                print("Scanning for devices...")
                # scan for devices
                while not connected_address:
                    devices = await BleakScanner.discover(1)
                    for d in devices:
                        if d.address in nicla_address:
                            device_name = d.name
                            connected_address = d.address
                            print(f"Found {device_name} at {d.address}")
                            await main_loop(connected_address)
                            break
                    else:
                        print("No SmartApples available found.")
        
            if connected_address is not None:
                await main_loop(connected_address)        

        except Exception as e:
            print(f"Unexpected error: {e}")
        except KeyboardInterrupt:
            print("Interrupted by user.")
        finally:
            print("Disconnected, cleaning up...")
            if ble_client:
                try:
                    await ble_client.stop_notify(SENSORS_UUID)
                    await ble_client.disconnect()
                    ble_client = None
                    connected_address = None
                    isStarted = False
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"Error during cleanup: {e}")

loop = asyncio.get_event_loop()

try:
    loop.run_until_complete(main())
finally:
    loop.close()
