import streamlit as st
import random
import string

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

# Function to create a fake list of BLE devices
def generate_fake_ble_devices(num_devices=5):
    fake_devices = []
    for _ in range(num_devices):
        device_name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        mac_address = ':'.join(''.join(random.choices(string.hexdigits.upper(), k=2)) for _ in range(6))
        fake_devices.append(f"{device_name} ({mac_address})")
    return fake_devices

# Add a title to your homepage
st.title("Home")

# Create a container for scanning BLE devices
ble_container = st.container()
with ble_container:
    st.header("Scan BLE Devices")
    col1, col2 = st.columns([0.09, 1])  # Create two columns to display the devices
    # Display a button and connect button
    with col1:
        reload_button = st.button("Refresh", key="reload_button")
    with col2:
        if 'selected_device' in st.session_state:
            connect_button = st.button("Connect", key="connect_button", disabled=st.session_state.get('enable_connect_button', False))
        else:
            connect_button = st.button("Connect", key="connect_button", disabled=True)

    # Reload button to refresh the list of BLE devices
    if reload_button:
        st.session_state.discovered_devices = generate_fake_ble_devices()

        # Use a radio button for device selection
        selected_device = st.radio("", st.session_state.discovered_devices)

        # Update selected_device in session state
        st.session_state.selected_device = selected_device
        # enable the connect button
        st.session_state.enable_connect_button = True
    
    # Connect button to connect to the selected device
    if connect_button:
        st.success(f"Connected to {st.session_state.selected_device}")
