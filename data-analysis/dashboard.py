import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objs as go
import plotly.express as px
import numpy as np
from scipy.interpolate import interp1d
import ruptures as rpt
import pandas as pd
import base64
import io
import os

app = dash.Dash(__name__)

df = None
df_stress = None
selected_row = 0

# Layout of the app
app.layout = html.Div([
    html.H1('Apple Impact Analysis', style={
        'textAlign': 'center',
        'fontFamily': 'Arial, Helvetica, sans-serif',
        'fontWeight': 'bold',
        'marginBottom': '1em',  # Adds space below the title
        'color': '#2c3e50'  # A professional dark blue shade
    }),

    dcc.Upload(
        id='upload-csv',
        children=html.Button('Upload CSV', id='upload-button', style={
            'color': 'white',
            'backgroundColor': '#3498db',  # A pleasant blue
            'border': 'none',
            'padding': '10px 20px',
            'textAlign': 'center',
            'textDecoration': 'none',
            'display': 'inline-block',
            'fontSize': '16px',
            'margin': '4px 2px',
            'cursor': 'pointer',
            'borderRadius': '5px',
            'fontWeight': 'bold'
        }),
        style={
            'width': '100%',
            'margin': '10px 0',
            'textAlign': 'center',  # Center the button if the width is less than 100%
        },
        multiple=False
    ),
    html.Div([
        dcc.Graph(id='sphere-plot',
                  style={'display': 'inline-block', 'width': '100%'}),
        dcc.Slider(
            id='sphere-resolution-slider',
            min=10,
            max=1000,
            step=10,
            value=60,
            marks={i: str(i) for i in range(10, 1001, 100)},
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
            marks={0: '0', 1: '1'},  # This will be updated with actual timestamps
        )
    ], style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'top'}),

    html.Div([
        dcc.Graph(id='zone-plot', style={'display': 'inline-block', 'width': '100%'}),
    ], style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'top'}),

    html.Div([
        dcc.Graph(id='deformation-plot', style={'display': 'inline-block', 'width': '100%'}),
    ], style={'width': '49%', 'display': 'inline-block', 'vertical-align': 'top'}),
])

# Callback to parse and load the CSV file and update plots based on sliders
@app.callback(
    Output('sphere-plot', 'figure'),
    Output('acceleration-plot', 'figure'),
    Output('deformation-plot', 'figure'),
    Output('zone-plot', 'figure'),
    Output('time-slider', 'max'),
    Output('time-slider', 'marks'),
    [Input('upload-csv', 'contents'),
     Input('sphere-resolution-slider', 'value'),
     Input('time-slider', 'value')],
    [State('upload-csv', 'filename'),
     State('acceleration-plot', 'figure'),
     State('deformation-plot', 'figure'),
     State('sphere-plot', 'figure')]
)
def update_output(contents, sphere_resolution, time_slider_value, filename, accel_figure, deformation_figure, sphere_figure):
    global df, df_stress
    ctx = callback_context

    # Process the CSV file upload
    if ctx.triggered and ctx.triggered[0]['prop_id'] == 'upload-csv.contents':
        if contents:

            # get stress-strain curve data
            curr_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(curr_dir, 'experimental_curve', 'stress_deformation_curve.csv')
            df_stress = pd.read_csv(data_dir, sep=',', header=1, names=['Deformation (mm)', 'Force (N)'])
            # interpolate points every 0.01 mm
            interp_x = np.arange(df_stress['Deformation (mm)'].min(), df_stress['Deformation (mm)'].max(), 0.01)
            interp_y = interp1d(df_stress['Deformation (mm)'], df_stress['Force (N)'], kind='linear')(interp_x)
            # Create new stress-strain curve DataFrame
            df_stress = pd.DataFrame({'Deformation (mm)': interp_x, 'Force (N)': interp_y})

            # print file name
            # print(filename)
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
 
            # convert the _time column to datetime for time series analysis
            df['_time'] = pd.to_datetime(df['_time'])

            # drop 'action' column
            if 'action' in df.columns:
                df = df.drop(columns=['action'])

            # find the clusters of the zones
            # calculate the magnitude of the acceleration and gyro
            df['accel_mag'] = np.sqrt(df['accel_x']**2 + df['accel_y']**2 + df['accel_z']**2)
            df['gyro_mag'] = np.sqrt(df['gyro_x']**2 + df['gyro_y']**2 + df['gyro_z']**2)

            num_zones = 4
            model = rpt.Window(model='l2').fit(df['accel_mag'].values)
            # Predict change points. This method takes the penalty value as an argument.
            change_points = model.predict(n_bkps=num_zones)
            # Create an array of zone labels based on the change points
            zone_labels = np.arange(len(change_points))
            # Initialize a new column 'infer_zone' in the DataFrame with zeros
            df['infer_zone'] = 0

            # Loop through the change points and assign the appropriate zone labels
            for i, change_point in enumerate(change_points):
                if i == 0:
                    df.loc[:change_point, 'infer_zone'] = zone_labels[i]
                else:
                    df.loc[change_points[i-1]:change_point, 'infer_zone'] = zone_labels[i]

            # drop the 'accel_mag' and 'gyro_mag' columns
            df = df.drop(columns=['accel_mag', 'gyro_mag'])
            # resample the data to 0.01s intervals
            sample_time = '0.01S'
            df = df.resample(sample_time, on='_time').mean()
            df = df.reset_index()

            # interpolate the data to fill in missing values
            df = df.interpolate(method='linear', limit_direction='both')
            df['magnitude'] = np.sqrt(df['accel_x']**2 + df['accel_y']**2 + df['accel_z']**2)
            critical_accel = 4.0
            df['critical_magnitude'] = np.clip(df['magnitude'], 0, critical_accel) / critical_accel
            df['infer_zone'] = df['infer_zone'].astype(int)
            # Define impact thresholds for impact detection
            critical_thresholds = [1.0, 2.0, 3.0]

            # Create a new column 'impact' with default value 0
            df['impact'] = 0

            # Loop through the thresholds and assign the appropriate impact values
            for i, threshold in enumerate(critical_thresholds):
                if i == 0:
                    df.loc[df['magnitude'] > threshold, 'impact'] = i + 1
                else:
                    df.loc[df['magnitude'] > threshold, 'impact'] = i + 1

           # Handle the case where magnitude is zero to avoid division by zero
            mask = df['magnitude'] != 0

            # Normalize the acceleration values only where magnitude is non-zero
            df.loc[mask, 'norm_accel_x'] = df.loc[mask, 'accel_x'] / df.loc[mask, 'magnitude']
            df.loc[mask, 'norm_accel_y'] = df.loc[mask, 'accel_y'] / df.loc[mask, 'magnitude']
            df.loc[mask, 'norm_accel_z'] = df.loc[mask, 'accel_z'] / df.loc[mask, 'magnitude']

            # Where magnitude is zero, set normalized accelerations to zero
            df.loc[~mask, 'norm_accel_x'] = 0
            df.loc[~mask, 'norm_accel_y'] = 0
            df.loc[~mask, 'norm_accel_z'] = 0

            # add deformation and force columns
            apple_mass = 0.2  # kg
            df['Force (N)'] = df['magnitude'] * 9.806 * apple_mass
            df['Deformation (mm)'] = df['Force (N)'].apply(interpolate_deformation)

            # Sphere plot
            sphere_figure = update_sphere(sphere_resolution)

            # Acceleration plot
            accel_figure = update_acceleration_plot(df, time_slider_value)

            # Deformation plot
            deformation_figure = update_deformation_plot(df, time_slider_value)

            # Zone plot
            zone_figure = update_zone_plot(df)

            # Update time slider max and marks
            max_time = (len(df['_time']) - 1)
            max_time_seconds = (len(df['_time']) - 1) * 0.01  # 0.01s time step
            # set max time slider value to max_time_seconds
            marks = {i: str(round(i, 2)) for i in np.linspace(0, max_time_seconds, 11)}

            return sphere_figure, accel_figure, deformation_figure, zone_figure, max_time_seconds, marks

    # Update sphere resolution
    elif ctx.triggered and ctx.triggered[0]['prop_id'] == 'sphere-resolution-slider.value' or \
            ctx.triggered and ctx.triggered[0]['prop_id'] == 'time-slider.value':
        
        sphere_figure = update_sphere(sphere_resolution)
        accel_figure = update_acceleration_plot(df, time_slider_value)
        deformation_figure = update_deformation_plot(df, time_slider_value)
        return sphere_figure, accel_figure, deformation_figure, dash.no_update, dash.no_update, dash.no_update

    raise dash.exceptions.PreventUpdate

def interpolate_deformation(force_n):
    global df_stress
    # Use your force-deformation data to interpolate the deformation
    if force_n < df_stress['Force (N)'].min():
        return df_stress['Deformation (mm)'].min()
    elif force_n > df_stress['Force (N)'].max():
        return df_stress['Deformation (mm)'].max()
    else:
        return np.interp(force_n, df_stress['Force (N)'], df_stress['Deformation (mm)'])

def update_zone_plot(df):
    # set colors [green, yellow, orange, red]
    colors = ['#00cc44', '#ffd633', '#ffa31a', '#ff3333']

    # plot histogram of the impact for each zone, zones are the x axis and the impact is the y axis
    fig = px.histogram(
        df,
        x='infer_zone',
        y='impact',
        color='impact',
        color_discrete_sequence=colors,
        # nbins=len(df['infer_zone'].unique()),
        labels={'infer_zone': 'Zone', 'impact': 'Impact'},
        title='Impact Distribution',
        # make the bars stacked
        barmode='stack',
        # remove the gap between bars
        # barnorm='percent',
        # show the counts
        histfunc='count',
    )

    # add title to layout
    fig.update_layout(
        title={
            'text': "Impact Distribution",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
        xaxis_title='Zone',
        yaxis_title='Impact',
        xaxis=dict(showline=True, showgrid=False, showticklabels=True, linecolor='rgb(204, 204, 204)', linewidth=2, ticks='outside', tickfont=dict(family='Arial', size=12, color='rgb(82, 82, 82)')),
        yaxis=dict(showgrid=False, zeroline=False, showline=False, showticklabels=True),
        autosize=True,
        margin=dict(autoexpand=True, l=100, r=20, t=110),
        bargap=0.2,
        # set x ticks
        xaxis_tickvals=df['infer_zone'].unique(),

    )

    return fig

def update_deformation_plot(df, time_slider_value):
    global selected_row
    # Deformation plot
    deformation_figure = go.Figure()

    # Add the line trace
    deformation_figure.add_trace(go.Scatter(
        x=df['_time'],
        y=df['Deformation (mm)'],
        mode='lines+markers',
        name='Deformation (mm)',
        marker=dict(
            size=5,
            color=df['Deformation (mm)'],  # Set color to the deformation values
            colorscale='Viridis',  # Color scale to use
            colorbar=dict(title='Deformation (mm)'),
            showscale=True
        ),
        line=dict(
            color='lightgrey'
        )
    ))

    # Determine the row index based on the slider value
    time_step = 0.01  # Time step in seconds
    row_index = int(time_slider_value / time_step)
    row_index = min(row_index, len(df) - 1)  # Ensure the index doesn't exceed the DataFrame length

    selected_row = row_index
    # Get the timestamp and deformation values at the determined row
    current_time = df['_time'].iloc[row_index]
    deformation_value = df['Deformation (mm)'].iloc[row_index]

    # Add a scatter point for the current time
    deformation_figure.add_trace(go.Scatter(
        x=[current_time],
        y=[deformation_value],
        mode='markers',
        marker=dict(
            color='red',
            size=5
        ),
        showlegend=False
    ))

    # Add a vertical line to indicate the current time
    deformation_figure.add_shape(
        type='line',
        x0=current_time, y0=df['Deformation (mm)'].min(),
        x1=current_time, y1=df['Deformation (mm)'].max(),
        line=dict(color='grey', width=1, dash='dot'),
        layer="below"
    )

    # Add title to layout
    deformation_figure.update_layout(
        title={
            'text': "Deformation Profile",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
        xaxis_title='Time',
        yaxis_title='Deformation (mm)',
        xaxis=dict(showline=True, showgrid=False, showticklabels=True, linecolor='rgb(204, 204, 204)', linewidth=2, ticks='outside', tickfont=dict(family='Arial', size=12, color='rgb(82, 82, 82)')),
        yaxis=dict(showgrid=False, zeroline=False, showline=False, showticklabels=True),
        autosize=True,
        margin=dict(autoexpand=True, l=100, r=20, t=110),
        showlegend=False,
        plot_bgcolor='white'
    )

    return deformation_figure

def update_acceleration_plot(df, time_slider_value):
    global selected_row
    # Acceleration plot
    accel_figure = go.Figure()
    accel_figure.add_trace(go.Scatter(x=df['_time'], y=df['accel_x'], mode='lines', name='Accel X'))
    accel_figure.add_trace(go.Scatter(x=df['_time'], y=df['accel_y'], mode='lines', name='Accel Y'))
    accel_figure.add_trace(go.Scatter(x=df['_time'], y=df['accel_z'], mode='lines', name='Accel Z'))

    # Determine the row index based on the slider value
    time_step = 0.01  # Time step in seconds
    row_index = int(time_slider_value / time_step)
    row_index = min(row_index, len(df) - 1)  # Ensure the index doesn't exceed the DataFrame length

    selected_row = row_index
    # Get the timestamp and acceleration values at the determined row
    current_time = df['_time'].iloc[row_index]
    accel_x_value = df['accel_x'].iloc[row_index]
    accel_y_value = df['accel_y'].iloc[row_index]
    accel_z_value = df['accel_z'].iloc[row_index]

    # Add a scatter point for each acceleration trace at the current time
    accel_figure.add_trace(go.Scatter(x=[current_time], y=[accel_x_value],
                                      mode='markers', marker=dict(color='blue', size=10),
                                      showlegend=False))
    accel_figure.add_trace(go.Scatter(x=[current_time], y=[accel_y_value],
                                      mode='markers', marker=dict(color='red', size=10),
                                      showlegend=False))
    accel_figure.add_trace(go.Scatter(x=[current_time], y=[accel_z_value],
                                      mode='markers', marker=dict(color='green', size=10),
                                      showlegend=False))

    # Add a vertical line to indicate the current time
    accel_figure.add_shape(
        type='line',
        x0=current_time, y0=min(df['accel_x'].min(), df['accel_y'].min(), df['accel_z'].min()),
        x1=current_time, y1=max(df['accel_x'].max(), df['accel_y'].max(), df['accel_z'].max()),
        line=dict(color='grey', width=1, dash='dot'),
        layer="below"
    )

    # add title to layout
    accel_figure.update_layout(
        title={
            'text': "Acceleration Profile",
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'}
    )

    return accel_figure

def update_sphere(resolution):
    global selected_row, df
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

    # Initialize a list to keep track of the closest triangles and their distances
    closest_triangles = []

    # Loop over the theta and phi angles
    for i in range(len(theta) - 1):
        for j in range(len(phi) - 1):
            # Append the indices of the vertices of each triangle
            triangles.append([i * len(phi) + j, (i + 1) * len(phi) + j, i * len(phi) + (j + 1)])
            triangles.append([(i + 1) * len(phi) + j, (i + 1) * len(phi) + (j + 1), i * len(phi) + (j + 1)])

            # Calculate the distance between the current point and the normalized acceleration vector
            dist = np.sqrt((df['norm_accel_x'].iloc[selected_row] - x[i][j])**2 +
                        (df['norm_accel_y'].iloc[selected_row] - y[i][j])**2 +
                        (df['norm_accel_z'].iloc[selected_row] - z[i][j])**2)

            # Append the triangle index and its distance to the list
            idx_triangle = len(triangles) - 2
            closest_triangles.append((idx_triangle, dist))
            closest_triangles.append((idx_triangle + 1, dist))


    # Sort the list by distance and get the top N triangles
    number_closest_triangles = int(df["critical_magnitude"].iloc[selected_row] * 1000)

    closest_triangles.sort(key=lambda x: x[1])
    top_triangles = [idx for idx, _ in closest_triangles[:number_closest_triangles]]

    # Convert to a numpy array
    triangles = np.array(triangles)

    # Initialize face colors and set the top N triangles to a shade of red
    face_colors = ['yellow'] * len(triangles)
    for idx in top_triangles:
        # color_intensity = int((1 - df["critical_magnitude"].iloc[selected_row]) * 255)
        color_intensity = 255
        face_colors[idx] = f'rgb({color_intensity}, 0, 0)'
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
        title='Acceleration Sphere',
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
