import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy.interpolate import interp1d
from scipy.signal import butter, filtfilt
import os

# get absolute path of the current directory
curr_dir = os.path.dirname(os.path.abspath(__file__))
file_name = 'processed_melinda_plant_2023-12-05_11-58.csv'
data_dir = os.path.join(curr_dir, 'acquisitions', file_name)

# Read the CSV file and create a DataFrame
df = pd.read_csv(data_dir)

# convert the _time column to datetime for time series analysis
df['_time'] = pd.to_datetime(df['_time'])
# keep only the '_time' and 'accel_x' columns
df = df[['_time', 'accel_x']]

sample_time = '0.01S'

# resample the data to 0.01s intervals
df = df.resample(sample_time, on='_time').mean()
df = df.reset_index()

# interpolate the data to fill in missing values
df['accel_x'] = df['accel_x'].interpolate(method='linear')

# plot the original data
sns.set()
plt.plot(df['_time'], df['accel_x'], label='Original Data')
plt.xlabel('Time')
plt.ylabel('Acceleration')
plt.title('Original Acceleration vs Time')
plt.legend()
plt.show()

# perform a fft on the original data
fft_original = np.fft.fft(df['accel_x'])
fft_original = np.abs(fft_original)
freq_original = np.fft.fftfreq(len(fft_original), float(sample_time[:-1]))

# Extract positive frequencies
mask_original = freq_original >= 0
freq_original = freq_original[mask_original]
fft_original = fft_original[mask_original]
psd_original = fft_original**2

# plot original power spectral density
plt.semilogy(freq_original, psd_original, label='Original PSD')
plt.xlabel('Frequency (Hz)')
plt.ylabel('PSD ($g^2$/Hz)')
plt.title('Original Power Spectrum')
plt.legend()
plt.show()

# Apply Butterworth low-pass filter
def butter_lowpass_filter(data, cutoff_freq, sample_rate, order=4):
    nyquist = 0.5 * sample_rate
    normal_cutoff = cutoff_freq / nyquist
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    filtered_data = filtfilt(b, a, data)
    return filtered_data

# Set cutoff frequency for the low-pass filter
cutoff_frequency = 10  # Adjust as needed

# Apply low-pass filter to the accelerometer data
df['accel_x_filtered'] = butter_lowpass_filter(df['accel_x'], cutoff_frequency, 1 / float(sample_time[:-1]))

# Plot the filtered data
plt.plot(df['_time'], df['accel_x_filtered'], label='Filtered Data')
plt.xlabel('Time')
plt.ylabel('Acceleration')
plt.title('Filtered Acceleration vs Time')
plt.legend()
plt.show()

# Perform FFT on the filtered data
# fft_filtered = np.fft.fft(df['accel_x_filtered'])
fft_filtered = np.fft.fft(df['accel_x'])
fft_filtered = np.abs(fft_filtered)
freq_filtered = np.fft.fftfreq(len(fft_filtered), float(sample_time[:-1]))

# Extract positive frequencies
mask_filtered = freq_filtered >= 0
freq_filtered = freq_filtered[mask_filtered]
fft_filtered = fft_filtered[mask_filtered]
psd_filtered = fft_filtered**2

# apply rolling mean to the filtered fft to smooth the data
window_size = 300
rolling_mean = np.convolve(psd_filtered, np.ones(window_size)/window_size, mode='same')

# plot the smoothed data
plt.semilogy(freq_filtered, psd_filtered, label='Filtered PSD')
plt.semilogy(freq_filtered, rolling_mean, label='Smoothed PSD')
plt.xlabel('Frequency (Hz)')
plt.ylabel('PSD ($g^2$/Hz)')
plt.title('Smoothed Power Spectrum')
plt.legend()
plt.show()
