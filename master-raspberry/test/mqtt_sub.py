import sys

import paho.mqtt.client as paho

nicla_address = ["EE:DF:46:E7:08:80", "9C:E3:E6:C9:4A:C8"]

def message_handling(client, userdata, msg):
    print(f"{msg.topic}: {msg.payload.decode()}")


client = paho.Client()
client.on_message = message_handling

if client.connect("localhost", 1883, 60) != 0:
    print("Couldn't connect to the mqtt broker")
    sys.exit(1)

for address in nicla_address:
    client.subscribe(f"nicla/{address}/movement_sensor_data", 0)

try:
    print("Press CTRL+C to exit...")
    client.loop_forever()
except Exception:
    print("Caught an Exception, something went wrong...")
finally:
    print("Disconnecting from the MQTT broker")
    client.disconnect()