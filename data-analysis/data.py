import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy.signal import welch
import os

# get absolute path of the current directory
curr_dir = os.path.dirname(os.path.abspath(__file__))
file_name = 'processed_throwing_xyz_2023-12-29_16-15-25.csv'
data_dir = os.path.join(curr_dir, 'acquisitions/synthetic_test/processed', file_name)

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

# save the interpolated data to a new csv file
# df.to_csv(curr_dir+'/acquisitions/synthetic_test/interpolated/interpolated_'+file_name, index=False)

# plot the original data
sns.set()
# plot accel_x, accel_y, accel_z and gyro_x, gyro_y, gyro_z in separate subplots
fig, (ax1, ax2) = plt.subplots(2, 1)
ax1.plot(df['_time'], df['accel_x'], label='accel_x')
ax1.plot(df['_time'], df['accel_y'], label='accel_y')
ax1.plot(df['_time'], df['accel_z'], label='accel_z')
ax1.set_ylabel('Acceleration [g]')
ax1.set_title('Acceleration')
ax1.legend()
ax2.plot(df['_time'], df['gyro_x'], label='gyro_x')
ax2.plot(df['_time'], df['gyro_y'], label='gyro_y')
ax2.plot(df['_time'], df['gyro_z'], label='gyro_z')
ax2.set_ylabel('Angular velocity [°/s]')
ax2.set_title('Angular velocity')
ax2.legend()
plt.show()

# perform a fft on each accelerometer and gyroscope axis
fft_accel_x = np.fft.fft(df['accel_x'])
fft_accel_y = np.fft.fft(df['accel_y'])
fft_accel_z = np.fft.fft(df['accel_z'])
fft_gyro_x = np.fft.fft(df['gyro_x'])
fft_gyro_y = np.fft.fft(df['gyro_y'])
fft_gyro_z = np.fft.fft(df['gyro_z'])

# calculate the frequency of each fft bin
fft_freq_accel_x = np.fft.fftfreq(len(df['accel_x']), float(sample_time[:-1]))
fft_freq_accel_y = np.fft.fftfreq(len(df['accel_y']), float(sample_time[:-1]))
fft_freq_accel_z = np.fft.fftfreq(len(df['accel_z']), float(sample_time[:-1]))
fft_freq_gyro_x = np.fft.fftfreq(len(df['gyro_x']), float(sample_time[:-1]))
fft_freq_gyro_y = np.fft.fftfreq(len(df['gyro_y']), float(sample_time[:-1]))
fft_freq_gyro_z = np.fft.fftfreq(len(df['gyro_z']), float(sample_time[:-1]))

# take only the positive frequencies
fft_accel_x = fft_accel_x[fft_freq_accel_x > 0]
fft_accel_y = fft_accel_y[fft_freq_accel_y > 0]
fft_accel_z = fft_accel_z[fft_freq_accel_z > 0]
fft_gyro_x = fft_gyro_x[fft_freq_gyro_x > 0]
fft_gyro_y = fft_gyro_y[fft_freq_gyro_y > 0]
fft_gyro_z = fft_gyro_z[fft_freq_gyro_z > 0]
fft_freq_accel_x = fft_freq_accel_x[fft_freq_accel_x > 0]
fft_freq_accel_y = fft_freq_accel_y[fft_freq_accel_y > 0]
fft_freq_accel_z = fft_freq_accel_z[fft_freq_accel_z > 0]
fft_freq_gyro_x = fft_freq_gyro_x[fft_freq_gyro_x > 0]
fft_freq_gyro_y = fft_freq_gyro_y[fft_freq_gyro_y > 0]
fft_freq_gyro_z = fft_freq_gyro_z[fft_freq_gyro_z > 0]

# calculate psd using Welch's method
f_accel_x, Pxx_den_accel_x = welch(df['accel_x'], 1 / float(sample_time[:-1]), nperseg=2048)
f_accel_y, Pxx_den_accel_y = welch(df['accel_y'], 1 / float(sample_time[:-1]), nperseg=2048)
f_accel_z, Pxx_den_accel_z = welch(df['accel_z'], 1 / float(sample_time[:-1]), nperseg=2048)
f_gyro_x, Pxx_den_gyro_x = welch(df['gyro_x'], 1 / float(sample_time[:-1]), nperseg=2048)
f_gyro_y, Pxx_den_gyro_y = welch(df['gyro_y'], 1 / float(sample_time[:-1]), nperseg=2048)
f_gyro_z, Pxx_den_gyro_z = welch(df['gyro_z'], 1 / float(sample_time[:-1]), nperseg=2048)

# plot the fft together with the psd for each accelerometer axis
fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2)
# plot accel_x
ax1.plot(fft_freq_accel_x, np.abs(fft_accel_x), label='accel_x', color='C0')
ax1.set_ylabel('Amplitude $[g]$')
ax1.legend()
ax1.set_title('FFT')
ax2.semilogy(f_accel_x, Pxx_den_accel_x, label='accel_x', color='C0')
ax2.set_ylabel('Power $[g^2/Hz]$')
ax2.legend()
ax2.set_title('PSD')
# plot accel_y
ax3.plot(fft_freq_accel_y, np.abs(fft_accel_y), label='accel_y', color='C1')
ax3.set_ylabel('Amplitude $[g]$')
ax3.legend()
ax4.semilogy(f_accel_y, Pxx_den_accel_y, label='accel_y', color='C1')
ax4.set_ylabel('Power $[g^2/Hz]$')
ax4.legend()
# plot accel_z
ax5.plot(fft_freq_accel_z, np.abs(fft_accel_z), label='accel_z', color='C2')
ax5.set_xlabel('Frequency [Hz]')
ax5.set_ylabel('Amplitude $[g]$')
ax5.legend()
ax6.semilogy(f_accel_z, Pxx_den_accel_z, label='accel_z', color='C2')
ax6.set_xlabel('Frequency [Hz]')
ax6.set_ylabel('Power $[g^2/Hz]$')
ax6.legend()
plt.show()

# plot the fft together with the psd for each gyroscope axis
fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2)
# plot gyro_x
ax1.plot(fft_freq_gyro_x, np.abs(fft_gyro_x), label='gyro_x', color='C0')
ax1.set_ylabel('Amplitude $[°/s]$')
ax1.legend()
ax1.set_title('FFT')
ax2.semilogy(f_gyro_x, Pxx_den_gyro_x, label='gyro_x', color='C0')
ax2.set_ylabel('Power $[(°/s)^2/Hz]$')
ax2.legend()
ax2.set_title('PSD')
# plot gyro_y
ax3.plot(fft_freq_gyro_y, np.abs(fft_gyro_y), label='gyro_y', color='C1')
ax3.set_ylabel('Amplitude $[°/s]$')
ax3.legend()
ax4.semilogy(f_gyro_y, Pxx_den_gyro_y, label='gyro_y', color='C1')
ax4.set_ylabel('Power $[(°/s)^2/Hz]$')
ax4.legend()
# plot gyro_z
ax5.plot(fft_freq_gyro_z, np.abs(fft_gyro_z), label='gyro_z', color='C2')
ax5.set_xlabel('Frequency [Hz]')
ax5.set_ylabel('Amplitude $[°/s]$')
ax5.legend()
ax6.semilogy(f_gyro_z, Pxx_den_gyro_z, label='gyro_z', color='C2')
ax6.set_xlabel('Frequency [Hz]')
ax6.set_ylabel('Power $[(°/s)^2/Hz]$')
ax6.legend()
plt.show()
