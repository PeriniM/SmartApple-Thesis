import os
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Get current directory and file directory
curr_dir = os.path.dirname(os.path.abspath(__file__))
date_folder = '20231205'
file_dir = os.path.join(curr_dir, 'acquisitions/onsite_test/raw/', date_folder)
processed_dir = os.path.join(curr_dir, 'acquisitions/onsite_test/processed', date_folder)

# Create the processed directory if it does not exist
if not os.path.exists(processed_dir):
    os.makedirs(processed_dir)

file_name = 'apple1_test1.csv'
# Read CSV file into a Pandas DataFrame
df = pd.read_csv(file_dir+'/'+file_name)

# Conversion factors from datasheet
accel_sensitivity = 4096.0  # Sensitivity for accelerometer in LSB/g
gyro_sensitivity = 16.4    # Sensitivity for gyroscope in LSB/°/s

# Convert accelerometer and gyroscope data to standard units
df['accel_x'] /= accel_sensitivity
df['accel_y'] /= accel_sensitivity
df['accel_z'] /= accel_sensitivity
df['gyro_x'] /= gyro_sensitivity
df['gyro_y'] /= gyro_sensitivity
df['gyro_z'] /= gyro_sensitivity

# Convert '_time' to datetime
df['_time'] = pd.to_datetime(df['_time'])

# add 1 hour to '_time' to convert from UTC to EST
df['_time'] += pd.Timedelta(hours=1)

# Calculate the time difference between each row and add it as a new column called 'time_diff'
df['time_diff'] = df['_time'].diff().dt.total_seconds().fillna(0)

# Exclude non-numeric columns from calculations
numeric_columns = df.select_dtypes(include=['float64']).columns
# remove 'packet_id' and 'quat_x', 'quat_y', 'quat_z', 'quat_w' from numeric_columns
numeric_columns = numeric_columns.drop(['quat_x', 'quat_y', 'quat_z', 'quat_w', 'time_diff'])

# save the processed data to a new csv file
df.to_csv(processed_dir +'/'+ file_name, index=False)

# Create a subplot with 3 rows and 1 column
fig = make_subplots(rows=3, cols=1)

# Define dropdown buttons for each sensor type
accel_dropdown = [dict(label='X direction', method='update', args=[{'visible': [True, False, False, True, False, False, True, False, False]}, {'title': 'X direction'}]),
                  dict(label='Y direction', method='update', args=[{'visible': [False, True, False, False, True, False, False, True, False]}, {'title': 'Y direction'}]),
                  dict(label='Z direction', method='update', args=[{'visible': [False, False, True, False, False, True, False, False, True]}, {'title': 'Z direction'}])]

# Add traces for each sensor type
fig.add_trace(go.Scatter(x=df['_time'], y=df['accel_x'], mode='lines', name='accel_x', visible=True, connectgaps=False), row=1, col=1)
fig.add_trace(go.Scatter(x=df['_time'], y=df['accel_y'], mode='lines', name='accel_y', visible=True, connectgaps=False), row=1, col=1)
fig.add_trace(go.Scatter(x=df['_time'], y=df['accel_z'], mode='lines', name='accel_z', visible=True, connectgaps=False), row=1, col=1)

fig.add_trace(go.Scatter(x=df['_time'], y=df['gyro_x'], mode='lines', name='gyro_x', visible=True, connectgaps=False), row=2, col=1)
fig.add_trace(go.Scatter(x=df['_time'], y=df['gyro_y'], mode='lines', name='gyro_y', visible=True, connectgaps=False), row=2, col=1)
fig.add_trace(go.Scatter(x=df['_time'], y=df['gyro_z'], mode='lines', name='gyro_z', visible=True, connectgaps=False), row=2, col=1)

fig.add_trace(go.Scatter(x=df['_time'], y=df['quat_x'], mode='lines', name='quat_x', visible=True, connectgaps=False), row=3, col=1)
fig.add_trace(go.Scatter(x=df['_time'], y=df['quat_y'], mode='lines', name='quat_y', visible=True, connectgaps=False), row=3, col=1)
fig.add_trace(go.Scatter(x=df['_time'], y=df['quat_z'], mode='lines', name='quat_z', visible=True, connectgaps=False), row=3, col=1)

# Add dropdown buttons for each sensor type
fig.update_layout(
    updatemenus=[
        dict(type='buttons', showactive=True, buttons=[dict(label='Show All', method='update', args=[{'visible': [True]*9}, {'title': 'Show All'}])], x=0.2, xanchor='left', y=1.1, yanchor='top'),
        dict(type='dropdown', active=0, buttons=accel_dropdown, x=0.3, xanchor='left', y=1.1, yanchor='top'),
    ]
)

# Update xaxis properties
fig.update_xaxes(title_text='Time', row=1, col=1)
fig.update_xaxes(title_text='Time', row=2, col=1)
fig.update_xaxes(title_text='Time', row=3, col=1)

# Update yaxis properties
fig.update_yaxes(title_text='Acceleration (g)', row=1, col=1)
fig.update_yaxes(title_text='Gyroscope (°/s)', row=2, col=1)
fig.update_yaxes(title_text='Quaternions', row=3, col=1)

# Update title and height
fig.update_layout(title_text='Sensor Data', height=1000)

# Show plot
fig.show()
