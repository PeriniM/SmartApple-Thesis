import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
import numpy as np

app = dash.Dash(__name__)

# Define the layout of the app
app.layout = html.Div([
    dcc.Upload(
        id='upload-csv',
        children=html.Button('Upload CSV', id='upload-button', n_clicks=0),
        # Allow multiple files to be uploaded
        multiple=False
    ),
    dcc.Graph(
        id='random-sphere',
        style={'height': '800px', 'width': '800px', 'position': 'relative'}  # Set the position to relative
    ),
    html.Div(
        dcc.Slider(
            id='resolution-slider',
            min=10,
            max=100,
            step=1,
            value=20,
            marks={i: str(i) for i in range(10, 101, 10)},
            vertical=True,
        ),
        style={
            'position': 'absolute',
            'right': '10px',
            'top': '0',
            'height': '800px',
            'zIndex': '10'  # Ensure the slider is above the graph
        }
    ),
], style={'position': 'relative', 'height': '800px'})

# Styling for the upload button
@app.callback(
    Output('upload-button', 'style'),
    [Input('upload-button', 'n_clicks')]
)
def style_upload_button(n_clicks):
    if n_clicks == 0:
        return {
            'width': '200px',
            'height': '50px',
            'lineHeight': '50px',
            'borderWidth': '0px',
            'borderRadius': '5px',
            'textAlign': 'center',
            'color': '#ffffff',
            'background-color': '#1f77b4',
            'cursor': 'pointer',
            'font-size': '18px'
        }
    else:
        return {
            'width': '200px',
            'height': '50px',
            'lineHeight': '50px',
            'borderWidth': '0px',
            'borderRadius': '5px',
            'textAlign': 'center',
            'color': '#ffffff',
            'background-color': '#1f77b4',
            'cursor': 'pointer',
            'font-size': '18px'
        }

# Callback to update the sphere based on the slider value
@app.callback(
    Output('random-sphere', 'figure'),
    [Input('resolution-slider', 'value')]
)
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

    # Create the figure with the layout and mesh data
    return {'data': [mesh], 'layout': layout}

# Run the server
if __name__ == '__main__':
    app.run_server(debug=True, port=8050)  # You can change the port number here
