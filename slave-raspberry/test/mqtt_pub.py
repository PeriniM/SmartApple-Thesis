import sys

import paho.mqtt.client as paho

client = paho.Client()

if client.connect("192.168.0.101", 1883, 60) != 0:
    print("Couldn't connect to the mqtt broker")
    sys.exit(1)

while True:
    client.publish("test_topic", "Hi, paho mqtt client works fine!", 0)
client.disconnect()