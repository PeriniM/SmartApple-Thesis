import asyncio
from bleak import BleakScanner
import matplotlib.pyplot as plt
import datetime
import csv
import os
import pandas as pd
import seaborn as sns
sns.set_theme(style="darkgrid")

target_device_name = 'Adamo'
measurements_per_distance = 10  # Number of measurements to take at each distance
range_dist = [0,20]
all_rssi_values = []
formatted_timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

curr_dir = os.path.dirname(os.path.abspath(__file__))
save_dir = os.path.join(curr_dir, 'acquisitions')

csv_filename = f"measurements_{formatted_timestamp}.csv"

display_flag = True
scan_flag = False

async def scan_for_distance(distance):
    collected_measurements = 0

    while collected_measurements < measurements_per_distance:
        devices = await BleakScanner.discover(timeout=0.1)
        timestamp = datetime.datetime.now().isoformat()  # ISO formatted current timestamp
        for device in devices:
            if device.name and target_device_name in device.name:
                print(f"Distance: {distance}m, {device.name}: {device.rssi} dBm")
                all_rssi_values.append((distance, device.rssi, timestamp))  # Save as a tuple (distance, RSSI, timestamp)
                collected_measurements += 1
                break
        await asyncio.sleep(0.1)

def save_to_csv(filename, distance):
    mode = "a" if distance != 0 else "w"  # Append if it's not the first distance, else write a new file

    save_path = os.path.join(save_dir, filename)
    with open(save_path, mode, newline='') as file:
        writer = csv.writer(file)
        
        # Write the header only if it's the first distance
        if distance == 0:
            writer.writerow(["Distance (m)", "RSSI (dBm)", "Timestamp"])
        
        # Only write the measurements for the current distance
        for entry in all_rssi_values[-measurements_per_distance:]:
            writer.writerow(entry)


def scan_plot():
    plt.figure()

    # Extract only the RSSI values for plotting
    rssi_only_values = [entry[1] for entry in all_rssi_values]

    distances = list(range(range_dist[0], range_dist[1]+1, 2))
    x_ticks = [i * measurements_per_distance for i in range(len(distances))]
    
    plt.plot(rssi_only_values, linewidth=2)
    plt.xticks(x_ticks, distances)  # Setting the x-ticks to represent the end of each distance's measurements

    plt.title(f'RSSI values for {target_device_name} over various distances')
    plt.xlabel('Distance (m)')
    plt.ylabel('RSSI (dBm)')
    plt.show()

# main
if __name__ == "__main__":
    if scan_flag:
        loop = asyncio.get_event_loop()

        for distance in range(range_dist[0], range_dist[1]+1, 2):  # from 0 to 20 meters, in steps of 2 meters
            input(f"Position the Arduino {distance} meters away. Press ENTER to start scanning...")
            loop.run_until_complete(scan_for_distance(distance))
            save_to_csv(csv_filename, distance)  # Save data after collecting measurements for the current distance

        scan_plot() # Plot the results

    if display_flag:
        data = pd.read_csv(os.path.join(save_dir, 'signal_strenth_test.csv'))
        # convert timestamp column to datetime
        data['timestamp'] = pd.to_datetime(data['timestamp'])

        # Converting the distance column to integers
        data['distance'] = data['distance'].astype(int)

        # Calculating the mean RSSI for each distance and type
        mean_rssi = data.groupby(['distance', 'type']).rssi.mean().reset_index()

        print(data)
        # Plotting the scatter plot and the line plot
        plt.figure(figsize=(12, 6))

        # Scatter plot
        sns.scatterplot(x='distance', y='rssi', hue='type', data=data, alpha=0.2)

        # Line plot for mean values
        sns.lineplot(x='distance', y='rssi', hue='type', data=mean_rssi, legend=False, lw=2)

        # Adding titles and labels
        plt.title('BLE Signal Strength vs Distance with Mean RSSI Lines')
        plt.xlabel('Distance')
        plt.ylabel('RSSI (dBm)')

        # x-ticks should be integers
        plt.xticks(list(range(0, 21, 2)))

        # Show the plot
        plt.show()
