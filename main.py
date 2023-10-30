import asyncio
from bleak import BleakClient, BleakScanner, BleakError
import re

# Precompiled regular expression pattern
pattern = re.compile(r'(\d+),G:([\d.-]+),([\d.-]+),([\d.-]+),A:([\d.-]+),([\d.-]+),([\d.-]+),Q:([\d.-]+),([\d.-]+),([\d.-]+),([\d.-]+)')

# 0 means stop notification, 1 means start notification
PROGRAM_COMMAND_UUID = "19b10000-8002-537e-4f6c-d104768a1214" 
SENSORS_UUID = "19b10000-A001-537e-4f6c-d104768a1214" # UUID to read from

nicla_address = "EE:DF:46:E7:08:80" # Nicla Sense Me device address
device_name = None
client = None
isStarted = False

def notification_handler(sender: int, data: bytearray):
    global pattern
    
    raw_data = data.decode('utf-8')
    match = pattern.match(raw_data)
    if match:
        packet_id, g_x, g_y, g_z, a_x, a_y, a_z, q_x, q_y, q_z, q_w = match.groups()
        print(f"Packet ID: {packet_id}")
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
                if client.is_connected:
                    print("Connected successfully!")
                    if not isStarted:
                        # send a byte 1 to start the program to the command characteristic
                        await client.write_gatt_char(PROGRAM_COMMAND_UUID, bytearray([1]))
                        isStarted = True
            
                    # start the sensors notification
                    await client.start_notify(SENSORS_UUID, notification_handler)

                    while client.is_connected:
                        await asyncio.sleep(1)
                else:
                    print("Failed to connect, retrying...")
                    await asyncio.sleep(2)
                    if isStarted:
                        isStarted = False
        except BleakError as e:
            print(f"BleakError while connecting: {e}")
        except Exception as e:
            print(f"Unexpected error while connecting: {e}")
        finally:
            print("Disconnected. Trying to reconnect...")
            await asyncio.sleep(2)
            if client:
                await client.stop_notify(SENSORS_UUID)
       
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
                    await client.stop_notify(SENSORS_UUID)
                    await client.disconnect()
                else:
                    print("Client is not connected.")
            except Exception as e:
                print(f"Error during cleanup: {e}")


loop = asyncio.get_event_loop()
loop.run_until_complete(main())

