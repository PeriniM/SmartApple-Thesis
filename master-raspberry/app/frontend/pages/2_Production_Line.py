import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd

# Set page config
st.set_page_config(
    page_title="SmartApple Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define custom styles for the containers
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Apply the custom styles defined in the 'style.css' file
local_css('style.css')

# Generate placeholder data
dates = pd.date_range(start="2023-01-01", periods=30, freq="D")
accel_x = np.random.uniform(low=30, high=70, size=len(dates))  # Simulate acceleration data
accel_y = np.random.uniform(low=30, high=70, size=len(dates))  # Simulate acceleration data
accel_z = np.random.uniform(low=350, high=450, size=len(dates))  # Simulate acceleration data
gyro_x = np.random.uniform(low=0, high=100, size=len(dates))  # Simulate gyro data
gyro_y = np.random.uniform(low=0, high=100, size=len(dates))  # Simulate gyro data
gyro_z = np.random.uniform(low=0, high=100, size=len(dates))  # Simulate gyro data
temperature = np.random.normal(loc=20, scale=3, size=len(dates))  # Simulate temperature data
humidity = np.random.uniform(low=30, high=70, size=len(dates))  # Simulate humidity data
co2_levels = np.random.uniform(low=350, high=450, size=len(dates))  # Simulate CO2 levels
air_quality = np.random.uniform(low=0, high=100, size=len(dates))  # Simulate air quality index

# Define a color scale for air quality - green for high quality, red for low
air_quality_color_scale = [
    (0.0, "red"),   # Air quality index 0
    (0.5, "yellow"), # Air quality index 50
    (1.0, "green"),  # Air quality index 100
]

# Main container for Nicla 1
with st.container():
    st.title("Production Line")
    # Create two rows for sensors display
    st.markdown("#### Section 1")
    with st.container():
        
        col1, col2 = st.columns(2)

        with col1:
            fig1 = go.Figure()
            # plot accel_x, accel_y, accel_z in the same figure
            fig1.add_trace(go.Scatter(x=dates, y=accel_x, mode='lines+markers', name='accel_x',
                                        line=dict(color='#1f77b4')))
            fig1.add_trace(go.Scatter(x=dates, y=accel_y, mode='lines+markers', name='accel_y',
                                        line=dict(color='#ff7f0e')))
            fig1.add_trace(go.Scatter(x=dates, y=accel_z, mode='lines+markers', name='accel_z',
                                        line=dict(color='#2ca02c')))
            fig1.update_layout(title='Acceleration', xaxis_title='Date', yaxis_title='Acceleration (m/s^2)', template="plotly_white")
            st.plotly_chart(fig1, use_container_width=True)
        
        # Create a line chart for Humidity
        with col2:
            fig2 = go.Figure()
            # plot gyro_x, gyro_y, gyro_z in the same figure
            fig2.add_trace(go.Scatter(x=dates, y=gyro_x, mode='lines+markers', name='gyro_x',
                                        line=dict(color='#1f77b4')))
            fig2.add_trace(go.Scatter(x=dates, y=gyro_y, mode='lines+markers', name='gyro_y',
                                        line=dict(color='#ff7f0e')))
            fig2.add_trace(go.Scatter(x=dates, y=gyro_z, mode='lines+markers', name='gyro_z',
                                        line=dict(color='#2ca02c')))
            fig2.update_layout(title='Gyroscope', xaxis_title='Date', yaxis_title='Gyroscope (°/s)', template="plotly_white")
            st.plotly_chart(fig2, use_container_width=True)
    
    with st.container():
        col3, col4 = st.columns(2)
        with col3:
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=dates, y=temperature, mode='lines+markers', name='Temperature',
                                      line=dict(color='#1f77b4')))
            fig3.update_layout(title='Temperature', xaxis_title='Date', yaxis_title='Temperature (°C)', template="plotly_white")
            st.plotly_chart(fig3, use_container_width=True)
        
        # Create a line chart for Humidity
        with col4:
            fig4 = go.Figure()
            fig4.add_trace(go.Scatter(x=dates, y=humidity, mode='lines+markers', name='Humidity',
                                      line=dict(color='#ff7f0e')))
            fig4.update_layout(title='Humidity', xaxis_title='Date', yaxis_title='Humidity (%)', template="plotly_white")
            st.plotly_chart(fig4, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="section-container">', unsafe_allow_html=True)
        st.markdown("#### Section 2")
        col3, col4 = st.columns(2)
        
        # Create a line chart for CO2 Level
        with col3:
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=dates, y=co2_levels, mode='lines+markers', name='CO2 Level',
                                      line=dict(color='#2ca02c')))
            fig3.update_layout(title='CO2 Level', xaxis_title='Date', yaxis_title='CO2 (PPM)', template="plotly_white")
            st.plotly_chart(fig3, use_container_width=True)
        
        # Create a line chart for Air Quality with gradient color
        with col4:
            fig4 = go.Figure(data=go.Scatter(
                x=dates,
                y=air_quality,
                mode='lines+markers',
                name='Air Quality',
                marker=dict(
                    size=8,
                    color=air_quality,  # Set color equal to a variable
                    colorscale=air_quality_color_scale,  # Set the colorscale
                    colorbar=dict(title='Air Quality'),
                    showscale=True
                ),
            ))
            fig4.update_layout(title='Air Quality', xaxis_title='Date', yaxis_title='AQI', template="plotly_white")
            st.plotly_chart(fig4, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
