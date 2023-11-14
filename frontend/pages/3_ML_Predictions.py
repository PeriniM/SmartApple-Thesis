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
power_consumption = np.random.normal(loc=500, scale=50, size=len(dates))  # Simulate power consumption
weather_forecast = np.random.uniform(low=10, high=30, size=len(dates))  # Simulate weather temperatures

# Main container for Machine Learning Impact Analysis
with st.container():
    st.title("Machine Learning Impact Analysis")
    col5, col6 = st.columns(2)
    
    # Create a line chart
    with col5:
        fig5 = go.Figure()
        fig5.add_trace(go.Scatter(x=dates, y=power_consumption, mode='lines+markers', name='Actual',
                                  line=dict(color='blue')))
        # Forecasted
        fig5.add_trace(go.Scatter(x=dates, y=power_consumption + np.random.normal(scale=20, size=len(dates)), mode='lines', name='Forecast',
                                  line=dict(color='orange')))
        fig5.update_layout(title='Time-series Forecast', xaxis_title='Date', yaxis_title='Power (kW)', template="plotly_white")
        st.plotly_chart(fig5, use_container_width=True)
    
    # Create a line chart for Forecasting
    with col6:
        fig6 = go.Figure()
        fig6.add_trace(go.Scatter(x=dates, y=weather_forecast, mode='lines', name='Forecast',
                                  fill='tozeroy', line=dict(color='skyblue')))
        fig6.update_layout(title='Forecast', xaxis_title='Date', yaxis_title='Temperature (°C)', template="plotly_white")
        st.plotly_chart(fig6, use_container_width=True)
