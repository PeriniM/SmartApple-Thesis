import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy.signal import welch
import os
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.tri as tri
from matplotlib import cm
from scipy.interpolate import Rbf
from matplotlib.animation import FuncAnimation
from matplotlib.animation import FFMpegWriter

# Change to reflect your file location!
plt.rcParams['animation.ffmpeg_path'] = 'D:\\ffmpeg\\bin\\ffmpeg.exe'
# get absolute path of the current directory
curr_dir = os.path.dirname(os.path.abspath(__file__))
file_name = 'processed_throwing_xyz_2023-12-29_16-15-25.csv'
save_dir = 'acquisitions/synthetic_test/processed'
data_dir = os.path.join(curr_dir, save_dir, file_name)
video_dir = os.path.join(curr_dir, save_dir, file_name[:-4]+'.mp4')
# Read the CSV file and create a DataFrame
df = pd.read_csv(data_dir)

# convert the _time column to datetime for time series analysis
df['_time'] = pd.to_datetime(df['_time'])
# remove 'packet_id' and 'time_diff' from dataframe
df = df.drop(['packet_id', 'time_diff'], axis=1)

# resample the data to 0.01s intervals
sample_time = '0.01S'
df = df.resample(sample_time, on='_time').mean()
df = df.reset_index()

# interpolate the data to fill in missing values
df = df.interpolate(method='linear', limit_direction='both')

critical_accel = 2.0

# Normalize the acceleration magnitudes
df['magnitude'] = np.sqrt(df['accel_x']**2 + df['accel_y']**2 + df['accel_z']**2)
df['normalized_magnitude'] = np.clip(df['magnitude'], 0, 2) / 2

metadata = dict(title='Acceleration Animation', artist='Matplotlib')
writer = FFMpegWriter(fps=100, metadata=metadata)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Set the axes properties
ax.set_xlim([-1, 1])
ax.set_ylim([-1, 1])
ax.set_zlim([-1, 1])
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.set_aspect('equal')

# Sphere parameters
radius = 0.5
u = np.linspace(0, 2 * np.pi, 100)
v = np.linspace(0, np.pi, 100)
x = radius * np.outer(np.cos(u), np.sin(v))
y = radius * np.outer(np.sin(u), np.sin(v))
z = radius * np.outer(np.ones(np.size(u)), np.cos(v))

with writer.saving(fig, "acceleration_animation.mp4", 100):
    for i in range(len(df)):
        print(f'Frame {i}')
        # Compute the color based on normalized magnitude
        norm = plt.Normalize(0, 1)
        color = plt.cm.viridis(norm(df['normalized_magnitude'].iloc[i]))

        # Clear the axes for the current frame
        ax.cla()
        
        # Re-establish the plot settings after clearing
        ax.set_xlim([-1, 1])
        ax.set_ylim([-1, 1])
        ax.set_zlim([-1, 1])
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_aspect('equal')

        # Plot the sphere
        ax.plot_surface(x, y, z, color='b', alpha=0.5, linewidth=0)
        
        # Plot the arrow representing the acceleration vector
        ax.quiver(0, 0, 0, df['accel_x'].iloc[i], df['accel_y'].iloc[i], df['accel_z'].iloc[i],
                  length=df['normalized_magnitude'].iloc[i], color=color, normalize=True)
        
        # Grab the frame
        writer.grab_frame()