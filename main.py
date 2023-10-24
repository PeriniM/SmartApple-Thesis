import asyncio
from bleak import BleakClient

# 0 means stop notification, 1 means start notification
PROGRAM_COMMAND_UUID = "19b10000-8002-537e-4f6c-d104768a1214" 
SENSORS_UUID = "19b10000-A001-537e-4f6c-d104768a1214" # UUID to read from
ADDRESS = "EE:DF:46:E7:08:80"  # Nicla Sense Me device address

def notification_handler(sender: int, data: bytearray):
    # print data (string ascii utf-8)
    print("data:", data.decode('utf-8'))
    
async def run(address):
    async with BleakClient(address) as client:
        # if client is connected send a byte 1 to start the program to the command characteristic
        await client.write_gatt_char(PROGRAM_COMMAND_UUID, bytearray([1]))
        # start the sensors notification
        await client.start_notify(SENSORS_UUID, notification_handler)
        await asyncio.sleep(30.0)  # Run for 30 seconds, or adjust as needed
        await client.write_gatt_char(PROGRAM_COMMAND_UUID, bytearray([0]))
       
asyncio.run(run(ADDRESS))

