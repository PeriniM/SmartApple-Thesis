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
        data = pd.read_csv(os.path.join(save_dir, 'signal_strength_test-all.csv'))
        # convert timestamp column to datetime
        data['timestamp'] = pd.to_datetime(data['timestamp'])

        # Converting the distance column to integers
        data['distance'] = data['distance'].astype(int)

        # Calculating the time difference between each reading
        data['time_diff'] = data.groupby(['distance', 'type'])['timestamp'].diff().dt.total_seconds()

        # Calculating the average time difference for each type at each distance
        avg_time_diff = data.groupby(['distance', 'type'])['time_diff'].mean().reset_index()

        # sort by type
        data = data.sort_values(by=['type'])
        # Calculating the mean RSSI for each distance and type
        mean_rssi = data.groupby(['distance', 'type']).rssi.mean().reset_index()

        # Getting unique types and distances for plotting
        types = avg_time_diff['type'].unique()
        distances = avg_time_diff['distance'].unique()

        palette = sns.color_palette("colorblind", len(types))

        # Plotting the scatter plot and the line plot
        plt.figure(figsize=(12, 6))

        # Scatter plot
        sns.scatterplot(x='distance', y='rssi', palette=palette, hue='type', data=data, legend=False, alpha=0.3, s=20)

        # Line plot for mean values
        sns.lineplot(x='distance', y='rssi', palette=palette, hue='type', data=mean_rssi, legend=True)

        # Adding titles and labels
        plt.title('BLE RSSI vs Distance')
        plt.xlabel('Distance (m)')
        plt.ylabel('RSSI (dBm)')

        # x-ticks should be integers
        plt.xticks(list(range(0, 21, 2)))
        plt.legend(loc='upper right')
        # Show the plot
        plt.show()

        # Creating the histogram grouped by type for each distance
        plt.figure(figsize=(12, 6))

        # Setting the width of the bars
        bar_width = 0.2

        # Enumerating over distances for grouping
        for i, d in enumerate(distances):
            for j, t in enumerate(types):
                # Compute the position for each bar
                bar_position = i - (len(types) / 2) * bar_width + j * bar_width

                # Extracting time difference for each type at this distance
                time_diff = avg_time_diff[(avg_time_diff['type'] == t) & (avg_time_diff['distance'] == d)]['time_diff'].values
                time_diff = time_diff[0] if len(time_diff) > 0 else 0

                # Plotting the bar
                plt.bar(bar_position, time_diff, width=bar_width, color=palette[j], label=t if i == 0 else "")

        # Adding titles and labels
        plt.title('BLE RSSI Time Interval vs Distance')
        plt.xlabel('Distance (m)')
        plt.ylabel('Average Time Interval (s)')

        # Setting the x-ticks to be the center of the group of bars for each distance
        plt.xticks([r for r in range(len(distances))], distances)

        # Adding a legend
        plt.legend(loc='upper right')

        # Show the plot
        plt.show()


