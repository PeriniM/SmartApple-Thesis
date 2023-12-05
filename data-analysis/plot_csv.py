import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Read CSV file into a Pandas DataFrame
df = pd.read_csv('acquisitions/melinda_plant_2023-12-05_11-58.csv')
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
fig.update_yaxes(title_text='Acceleration', row=1, col=1)
fig.update_yaxes(title_text='Gyroscope', row=2, col=1)
fig.update_yaxes(title_text='Quaternions', row=3, col=1)

# Update title and height
fig.update_layout(title_text='Sensor Data', height=1000)

# Show plot
fig.show()
