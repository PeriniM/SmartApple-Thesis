import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d
import os

# get absolute path of the current directory
curr_dir = os.path.dirname(os.path.abspath(__file__))
file_name = 'stress_deformation_curve.csv'
data_dir = os.path.join(curr_dir, file_name)

# Create a DataFrame
df = pd.read_csv(data_dir, sep=',', header=1, names=['Deformation (mm)', 'Force (N)'])

# Interpolate points every 0.01 mm
interp_x = np.arange(df['Deformation (mm)'].min(), df['Deformation (mm)'].max(), 0.01)
interp_y = interp1d(df['Deformation (mm)'], df['Force (N)'], kind='linear')(interp_x)
sns.set()
# Plot using Seaborn
plt.plot(interp_x, interp_y, linestyle='solid', label='Interpolated Line')
sns.scatterplot(x='Deformation (mm)', y='Force (N)', data=df, color='red', label='Original Points')

# Add text annotation for the source
source_text = 'Source: Deformation behaviour simulation of an apple under drop case by finite element method'
plt.annotate(source_text, xy=(0.5, -0.1), xycoords="axes fraction", ha="center", va="center", fontsize=8, color='black')

plt.title('Force-Deformation Curve of an Apple')
plt.legend()
plt.show()
