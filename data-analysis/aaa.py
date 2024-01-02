import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objs as go
import numpy as np
import pandas as pd
import base64
import io

app = dash.Dash(__name__)

df = None
current_time = None

# Layout of the app
app.layout = html.Div([
    dcc.Upload(
        id='upload-csv',
        children=html.Button('Upload CSV', id='upload-button'),
        style={'width': '100%', 'margin': '10px 0'},
        multiple=False
    ),
    html.Div([
        dcc.Graph(id='sphere-plot',
                  style={'display': 'inline-block', 'width': '100%'}),
        dcc.Slider(
            id='sphere-resolution-slider',
            min=10,
            max=100,
            step=1,
            value=20,
            marks={i: str(i) for i in range(10, 101, 10)}
        )
    ], style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'top'}),
    html.Div([
        dcc.Graph(id='acceleration-plot', style={'display': 'inline-block', 'width': '100%'}),
        dcc.Slider(
            id='time-slider',
            min=0,
            max=1,  # Updated based on the data
            value=0,
            step=0.01,
            marks={0: '0', 1: '1'}  # This will be updated with actual timestamps
        )
    ], style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'top'})
])

# Callback to parse and load the CSV file and update plots based on sliders
@app.callback(
    Output('sphere-plot', 'figure'),
    Output('acceleration-plot', 'figure'),
    Output('time-slider', 'max'),
    Output('time-slider', 'marks'),
    [Input('upload-csv', 'contents'),
     Input('sphere-resolution-slider', 'value'),
     Input('time-slider', 'value')],
    [State('upload-csv', 'filename'),
     State('acceleration-plot', 'figure')]
)
def update_output(contents, sphere_resolution, time_slider_value, filename, existing_accel_figure):
    global df, current_time
    ctx = callback_context

    # Process the CSV file upload
    if ctx.triggered and ctx.triggered[0]['prop_id'] == 'upload-csv.contents':
        if contents:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
 
            # convert the _time column to datetime for time series analysis
            df['_time'] = pd.to_datetime(df['_time'])

            # resample the data to 0.01s intervals
            sample_time = '0.01S'
            df = df.resample(sample_time, on='_time').mean()
            df = df.reset_index()

            # interpolate the data to fill in missing values
            df = df.interpolate(method='linear', limit_direction='both')
            df['magnitude'] = np.sqrt(df['accel_x']**2 + df['accel_y']**2 + df['accel_z']**2)
            critical_accel = 2.0
            df['normalized_magnitude'] = np.clip(df['magnitude'], 0, critical_accel) / critical_accel

            # Sphere plot
            sphere_figure = update_sphere(sphere_resolution)

            # Acceleration plot
            accel_figure = update_acceleration_plot(df, time_slider_value)

            # Update time slider max and marks
            max_time = (len(df['_time']) - 1)
            max_time_seconds = (len(df['_time']) - 1) * 0.01  # 0.01s time step
            # update the marks only with minute and second values
            marks = {}
            for i in range(0, max_time + 1, 100):
                time = df['_time'].iloc[i]
                marks[i] = f'{time.minute:02}:{time.second:02}'
            marks[max_time] = f'{df["_time"].iloc[max_time].minute:02}:{df["_time"].iloc[max_time].second:02}'

            return sphere_figure, accel_figure, max_time_seconds, marks

    # Update sphere resolution
    elif ctx.triggered and ctx.triggered[0]['prop_id'] == 'sphere-resolution-slider.value':
        sphere_figure = update_sphere(sphere_resolution)
        return sphere_figure, dash.no_update, dash.no_update, dash.no_update

    # Update acceleration plot based on time slider
    elif ctx.triggered and ctx.triggered[0]['prop_id'] == 'time-slider.value':
        accel_figure = update_acceleration_plot(df, time_slider_value)
        return dash.no_update, accel_figure, dash.no_update, dash.no_update

    raise dash.exceptions.PreventUpdate

def update_acceleration_plot(df, time_slider_value):
    # Acceleration plot
    accel_figure = go.Figure()
    accel_figure.add_trace(go.Scatter(x=df['_time'], y=df['accel_x'], mode='lines', name='Accel X'))
    accel_figure.add_trace(go.Scatter(x=df['_time'], y=df['accel_y'], mode='lines', name='Accel Y'))
    accel_figure.add_trace(go.Scatter(x=df['_time'], y=df['accel_z'], mode='lines', name='Accel Z'))

    # Determine the row index based on the slider value
    time_step = 0.01  # Time step in seconds
    print(f'time_slider_value: {time_slider_value}')
    row_index = int(round(time_slider_value / time_step))
    row_index = min(row_index, len(df) - 1)  # Ensure the index doesn't exceed the DataFrame length

    # Get the timestamp at the determined row
    current_time = df['_time'].iloc[row_index]

    # Add a vertical line
    accel_figure.add_shape(
        type='line',
        x0=current_time,
        y0=-max(df['accel_x'].max(), df['accel_y'].max(), df['accel_z'].max()),
        x1=current_time,
        y1=max(df['accel_x'].max(), df['accel_y'].max(), df['accel_z'].max()),
        line=dict(
            color='Red',
            width=2
        )
    )

    return accel_figure

def update_sphere(resolution):
    # Sphere parameters
    radius = 1
    theta = np.linspace(0, 2 * np.pi, resolution)
    phi = np.linspace(0, np.pi, resolution)
    theta, phi = np.meshgrid(theta, phi)
    x = radius * np.sin(phi) * np.cos(theta)
    y = radius * np.sin(phi) * np.sin(theta)
    z = radius * np.cos(phi)

    # Flatten the arrays for triangulation
    x_flat = x.flatten()
    y_flat = y.flatten()
    z_flat = z.flatten()

    # Create a triangulation of the sphere's surface
    triangles = []

    # Loop over the theta and phi angles
    for i in range(len(theta) - 1):
        for j in range(len(phi) - 1):
            # Append the indices of the vertices of each triangle
            triangles.append([i * len(phi) + j, (i + 1) * len(phi) + j, i * len(phi) + (j + 1)])
            triangles.append([(i + 1) * len(phi) + j, (i + 1) * len(phi) + (j + 1), i * len(phi) + (j + 1)])

    # Convert to a numpy array
    triangles = np.array(triangles)

    # Generate a random color for each triangle
    face_colors = np.random.choice(range(256), size=(triangles.shape[0], 3))
    face_colors = ['rgb({},{},{})'.format(r, g, b) for r, g, b in face_colors]

    # Create the mesh object
    mesh = go.Mesh3d(
        x=x_flat,
        y=y_flat,
        z=z_flat,
        i=triangles[:,0],
        j=triangles[:,1],
        k=triangles[:,2],
        facecolor=face_colors
    )

    # Define the layout for the plot
    layout = go.Layout(
        title='Randomly Colored Sphere',
        scene=dict(
            xaxis=dict(title='X'),
            yaxis=dict(title='Y'),
            zaxis=dict(title='Z'),
            aspectratio=dict(x=1, y=1, z=1)
        )
    )

    # Axes traces
    axis_length = 1.5 * radius  # Length of the axes
    axes = {
        'x': {'color': 'blue', 'vec': np.array([axis_length, 0, 0])},
        'y': {'color': 'red', 'vec': np.array([0, axis_length, 0])},
        'z': {'color': 'green', 'vec': np.array([0, 0, axis_length])},
    }

    axis_traces = []
    for k, v in axes.items():
        axis_trace = go.Scatter3d(
            x=[0, v['vec'][0]],
            y=[0, v['vec'][1]],
            z=[0, v['vec'][2]],
            mode='lines',
            line=dict(color=v['color'], width=4),
            name=f'{k}-axis'
        )
        axis_traces.append(axis_trace)

    # Add axis_traces to the data list
    data = [mesh] + axis_traces
    # Create the figure with the layout and mesh data
    return {'data': data, 'layout': layout}

# Run the server
if __name__ == '__main__':
    app.run_server(debug=True)
