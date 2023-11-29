#!/bin/bash

# Update and upgrade system packages
sudo apt-get update
sudo apt-get upgrade -y

# Prompt the user to choose whether it's for master or slave
read -p "Is this setup for the master or a slave? (master/slave): " target

# Define the source and destination directories based on the user's choice
if [[ "$target" == "master" ]]; then
    source_dir="./master-raspberry/config"
elif [[ "$target" == "slave" ]]; then
    source_dir="./slave-raspberry/config"
else
    echo "Invalid choice. Exiting."
    exit 1
fi

echo "Installing Docker and docker-compose..."
# Install Docker
curl -sSL https://get.docker.com | sh
sudo usermod -aG docker pi
# Install docker-compose
sudo apt-get install -y libffi-dev libssl-dev
sudo apt-get install -y python python-pip
sudo apt-get install -y python3 docker-compose

# echo "Changing DNS rules..."
# # Change DNS rules
# sudo sed -i 's/#DNS=/DNS=8.8.8.8 8.8.4.4/' /etc/systemd/resolved.conf
# sudo systemctl restart systemd-resolved.service

echo "Copying service files from $source_dir to /etc/systemd/system/"

# Copy .service files
sudo cp $source_dir/*.service /etc/systemd/system/

# Reload systemd to read the new service files
sudo systemctl daemon-reload

# enable the service to run on boot
sudo systemctl enable docker-compose-app.service
sudo systemctl enable wifi-power-management.service

# Create a Python virtual environment
python -m venv env

# Activate the virtual environment
source env/bin/activate

# Install Python requirements
pip install -r requirements.txt

# Provide instructions to the user
echo "Setup completed successfully! Rebooting..."

# Reboot the system
sudo reboot
