import sys
import paho.mqtt.client as paho

nicla_address = ["EE:DF:46:E7:08:80", "9C:E3:E6:C9:4A:C8"]
prod_line_id = ["test", "test"]

client = paho.Client()

if client.connect("localhost", 1883, 60) != 0:
    print("Couldn't connect to the MQTT broker")
    sys.exit(1)

try:
    while True:
        # Wait for user input for the production line string
        prod_line_string = input("Production line id: ")

        # Choose the appropriate NICLA address and production line ID based on the user's input
        nicla_index = int(input("Nicla index (0 or 1): "))
        nicla_address_selected = nicla_address[nicla_index]
        prod_line_id_selected = prod_line_id[nicla_index]

        # Publish the production line string to the MQTT topic
        topic = f"nicla/{nicla_address_selected}/prod_line"
        client.publish(topic, prod_line_string, 0)

except KeyboardInterrupt:
    print("\nUser interrupted. Disconnecting from MQTT broker.")

finally:
    client.disconnect()
