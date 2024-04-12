# IoT Sensor System for Fruit Stress Monitoring in Apple Grading Industrial Processes

The project aims to develop a system to monitor the stress of apples during the grading process in industrial plants. The system is composed of three main components: the Smart Apple, the IoT Gateway, and the IoT Server. The Smart Apple is a low-cost IoT device placed inside a real apple that measures the accelerations and angular velocities of the fruit and sends the data to the IoT Gateway. The IoT Gateway is a Raspberry Pi that collects the data from the Smart Apples and sends it to the IoT Server. The IoT Server is a Raspberry Pi that stores the data in a InfluxDB database and provides a web interface to visualize the data with some impact analyses. The system is designed to be scalable and easy to deploy in industrial environments.

# Operational steps

## Option 1 - Only Master

- Run directly the script located in data-analysis/acquisition_app.py
- It will start looking for Smart Apples (Arduino Nicla) with a known MAC address and start the streaming of the BLE packets
- We can save the data in a local csv (by setting the save2local flag), send it to a MQTT server (by setting the send2mqtt flag) or save it directly in the InfluxDB database (by setting the send2influxdb flag). You can also decide to activate all of them at the same time
- The data saved in InfluxDB can be retrieve using the master-raspberry/test/pull_influxdb.py script (be careful of the timestamp since there is no RTC module in the Raspberry Pi and therefore it would be the best to take the last few hours or minutes instead of specifying a range).

## Option 2 - Slave & Master

- **Raspberry Pi Master**
    - Run the script located in master-raspberry/app/main.py
    - It will start listening to the MQTT topic and when some data is received, it will push them to the InfluxDB database
- **Raspberry Pi Slave**
    - Run the script located in slave-raspberry/app/main.py
    - It will start looking for Smart Apples (Arduino Nicla) with a known MAC address and start the streaming of the BLE packets
    - After receiving some packets, it will write them on the MQTT topic
- The data saved in InfluxDB can be retrieve using the master-raspberry/test/pull_influxdb.py script (be careful of the timestamp since there is no RTC module in the Raspberry Pi and therefore it would be the best to take the last few hours or minutes instead of specifying a range)

# Raspberry Pi 4 Set-up

## Common Set-up

### Set-up Modem
- Enable only 2.4 GHz with a 20MHz bandwidth (disable automatic switching from 20MHz to 40MHz)
- Fix the wifi channel and disable the automatic switching
### Installing OS
- Install [Raspberry Pi Imager](https://www.raspberrypi.com/software/) and open it
- Press **CTRL+Shift+X** and modify the preferences enabling the WI-FI options
- If using the modem provided by the lab the credentials are:
    
    ```bash
    ssid: UNITN-SHIELD4US-WIFI
    password: 
    ```
    
- Enable SSH options and give a username and password, such as:
    
    ```bash
    user: pi
    hostname: raspPi01
    password: raspberry
    ```
    
- Select **RASPBERRY PI OS (64-BIT)**
- Press **WRITE** to flash the micro-SD
- If you want to add new wifi credentials, you can create a wpa_supplicant.conf file and place it in the root of the sd, with this content:
    ```bash
    ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
    update_config=1
    
    network={
        ssid="UNITN-SHIELD4US-WIFI"
        psk=""
        id_str="portable_router"
    }
    
    network={
        ssid="PROVA-SSID"
        psk="PASSWORD"
        id_str="prova_access_point"
    }
    ```
### Update BLE stack
- I have found that the bluez version **5.66** works better than others, so let’s update it (my current raspberry kernel is **6.1.21-v8+,** [Troubleshooting — bleak 0.21.1 documentation](https://bleak.readthedocs.io/en/latest/troubleshooting.html))
    
    ```bash
    # download new version
    wget http://www.kernel.org/pub/linux/bluetooth/bluez-5.66.tar.xz
    
    # extract it and go inside the folder
    tar xvf bluez-5.66.tar.xz
    cd bluez-5.66
    
    # install or update necessary dependencies
    sudo apt-get install libdbus-1-dev libglib2.0-dev libudev-dev libical-dev libreadline-dev
    
    # configure, compile and install
    ./configure --prefix=/usr --mandir=/usr/share/man --sysconfdir=/etc --localstatedir=/var --enable-experimental
    make
    sudo make install
    
    # restart the bluetooth services
    sudo systemctl daemon-reload
    sudo systemctl restart bluetooth
    
    # check bluez version
    bluetoothd -v
    # check kernel version
    uname -r
    
    # remove tar and folder
    cd ..
    rm bluez-5.66 -r && rm bluez-5.66.tar.xz
    ```
    
### Disable Wifi Power Management
    
Sometimes the Raspberry disconnects on its own from the network when it is in idle. To avoid this problem we can disable the wifi power management.

- Disable it temporally
    
    ```bash
    # check if it is on
    iwconfig wlan0 | grep "Power Management"
    # disable it
    sudo iwconfig wlan0 power off
    ```
    
- To disable it every time on start-up set-up a systemctl daemon
    
    ```bash
    # create a file
    sudo nano /etc/systemd/system/wifi-power-management.service
    
    # content of file
    [Unit]
    Description=Disable power management for wifi
    
    [Service]
    ExecStart=/sbin/iwconfig wlan0 power off
    Type=oneshot
    
    [Install]
    WantedBy=multi-user.target
    
    # save the file and enable the service
    sudo systemctl enable wifi-power-management.service
    # if you want to start it right away
    sudo systemctl start wifi-power-management.service
    ```
    
### Dependencies Installation
- update and upgrade packages
    
    ```bash
    sudo apt-get update 
    sudo apt-get upgrade
    ```
    
- clone github repo and install the dependencies
    
    ```bash
    # clone repo
    # insert github username and password (public token) if requested
    git clone https://github.com/PeriniM/SmartApple-Thesis.git
    
    # run bash to install everything and select whether the device is a Gateway or Server
    cd ./SmartApple-Thesis
    sudo chmod +x setup.sh
    ./setup.sh
    ```
    
- to discard local changes and fetch updated github repo
    
    ```bash
    git fetch --all
    git reset --hard origin/main
    ```
    

## IoT Gateway

### Using External Bluetooth Antenna
- the antenna must be compatible with bluetooth 5.0 to support BLE
- disable built-in interface to use the external antenna
        
    ```bash
    # check built-in interface name
    hciconfig
    
    # disable it to use new one
    sudo hciconfig hci0 down
    ```
        
### Run script on boot

## IoT Server

### Docker Influxdb, Grafana and Mosquitto
    
The following commands will set-up influxdb and grafana to run on boot inside a docker container

- install docker
        
    ```bash
    # install docker
    curl -sSL https://get.docker.com | sh
    sudo usermod -aG docker pi
    
    # reboot
    sudo reboot
    
    # install docker compose
    # sudo apt-get install libffi-dev libssl-dev
    # sudo apt-get install -y python python-pip
    sudo pip install docker-compose
    ```
        
- create the container
        
    ```bash
    # go inside the project folder and create the containers
    docker-compose up -d --build
    
    # stop the running containers
    docker-compose down
    ```
        
- if you get errors while installing, you need to set up the DNS properly
        
    ```bash
    # Open the systemd-resolved configuration file
    sudo nano /etc/systemd/resolved.conf
    # uncomment the DNS line and add the google ip
    DNS=8.8.8.8 8.8.4.4
    # restart the service
    sudo systemctl restart systemd-resolved
    # to verify the new DNS conf
    systemd-resolve --status
    ```
        
- to run on boot
        
    ```bash
    # create a systemd service file
    sudo nano /etc/systemd/system/docker-compose-app.service
    
    # content of the file
    [Unit]
    Description=Docker Compose Application Service
    Requires=docker.service
    After=docker.service
    
    [Service]
    WorkingDirectory=/home/pi/Desktop/SmartApple-Thesis
    ExecStart=/usr/local/bin/docker-compose up
    ExecStop=/usr/local/bin/docker-compose down
    TimeoutStartSec=0
    Restart=always
    RemainAfterExit=yes
    
    [Install]
    WantedBy=multi-user.target
    
    # reload systemd to read the new service
    sudo systemctl daemon-reload
    
    # enable the service to run on boot
    sudo systemctl enable docker-compose-app.service
    
    # start, stop, status service command
    sudo systemctl start docker-compose-app.service
    sudo systemctl stop docker-compose-app.service
    sudo systemctl status docker-compose-app.service
    ```
        
- if you make some changes to the docker-compose.yml
        
    ```bash
    # before making changes stop the service
    sudo systemctl stop docker-compose-app.service
    # apply changes to docker-compose file and run
    docker-compose up -d
    # restart systemctl service
    sudo systemctl restart docker-compose-app.service
    # to see if everything is good
    docker-compose logs
    ```
        
- to stop and remove all the containers
        
    ```bash
    docker container stop $(docker container ls -aq)
    docker container prune -f
    ```
        
### Set datetime
- If not accessed to internet to set manually the time we can use:
        
    ```bash
    sudo date -s '2024-01-26 13:04:00’
    ```
        
### Run script on boot

## Extras

### Enabling VNC
1. Connect through SSH using a terminal or Putty
    
    ```bash
    ssh pi@raspberrypi.local
    password: raspberry
    ```
    
2. Update the dependencies, create a folder for autoboot applications and install LXSession
    
    ```bash
    sudo apt-get update
    sudo mkdir -p /etc/xdg/autostart/
    sudo apt-get install lxsession
    ```
    
3. Open the options interface using ***sudo raspi-config*** and set the following to enable the GUI remote control:
    1. System Options > Boot / Auto Login > Desktop Autologin
    2. Display Options > VNC Resolution > 1920x1080
    3. Interface Options > VNC
4. Reboot with ***sudo reboot***
5. Download VNC Viewer, create an account and use the IP address of the raspberry to connect remotely to the GUI. To discover your device IP use the following command:
    
    ```bash
    ifconfig
    --OR--
    hostname -I
    ```
    
### Install Node-RED
    
```bash
bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered)
# to start local server
node-red-pi --max-old-space-size=256
```
    
### Raspberry Pi Zero W (WORKING)
1. Install the OS
2. Check if the bluetooth interface is available and enable BLE features
        
    ```bash
    # install bluetooth dependencies ([here](https://github.com/noble/noble))
    sudo apt-get install bluetooth bluez libbluetooth-dev libudev-dev
    # check if hci is available
    hcitool dev
    # check if bluetooth service is active
    sudo systemctl status bluetooth
    # if not, active it with
    sudo systemctl start bluetooth
    # open bluetooth.service file and add the --experimental flag for BLE
    sudo nano /lib/systemd/system/bluetooth.service
    'ExecStart=/usr/local/libexec/bluetooth/bluetoothd --experimental'
    
    # reload the configuration and restart the service
    sudo systemctl daemon-reload
    sudo systemctl restart bluetooth
    
    # set bluetoothd permission (found [here](https://flows.nodered.org/node/node-red-contrib-generic-ble))
    sudo usermod -G bluetooth -a pi
    
    # start/stop BLE advertising without sudo (found [here](https://flows.nodered.org/node/node-red-contrib-ble-sense))
    sudo setcap cap_net_raw+eip $(eval readlink -f `which node`)
    
    # reboot
    sudo reboot
    ```
        
3. Install Node-RED
4. Install **node-red-contrib-ble-sense** module and **dashboard**
        
### Install BLE dependencies on Raspberry Pi 3 (NOT WORKING)
- To upgrade or downgrade bluez package (guide [here](https://learn.adafruit.com/install-bluez-on-the-raspberry-pi/installation)):
        
    ```bash
    # install latest bluez version (check [here](http://www.bluez.org/download/))
    cd ~
    wget http://www.kernel.org/pub/linux/bluetooth/bluez-5.66.tar.xz
    tar xvf bluez-5.66.tar.xz && cd bluez-5.66
    
    # install dependencies
    sudo apt-get update
    sudo apt-get install -y libusb-dev libdbus-1-dev libglib2.0-dev libudev-dev libical-dev libreadline-dev
    
    # set configure method
    ./configure --enable-library
    
    # compile
    make
    
    # install package
    sudo make install
    
    # reboot
    sudo reboot
    
    # make the service start from boot
    sudo systemctl enable bluetooth
    
    # open bluetooth.service file and add the --experimental flag for BLE
    sudo nano /lib/systemd/system/bluetooth.service
    'ExecStart=/usr/local/libexec/bluetooth/bluetoothd --experimental'
    
    # reload the configuration and restart the service
    sudo systemctl daemon-reload
    sudo systemctl restart bluetooth
    
    # reboot
    sudo reboot
    ```
        
- To enable bluetooth:
        
    ```bash
    # set bluetoothd permission (found [here](https://flows.nodered.org/node/node-red-contrib-generic-ble))
    sudo usermod -G bluetooth -a pi
    sudo reboot
    
    # start/stop BLE advertising without sudo (found [here](https://flows.nodered.org/node/node-red-contrib-ble-sense))
    sudo setcap cap_net_raw+eip $(eval readlink -f `which node`)
    
    # install bluetooth dependencies
    sudo apt-get install bluetooth bluez libbluetooth-dev libudev-dev
    
    # check if bluetooth service is active
    sudo systemctl status bluetooth
    # if not, active it with
    sudo systemctl start bluetooth
    ```
        
### Bluez Raspberry Problem
- Install bleak (in a virtual environment or globally with sudo)
- When I run the python script with the bleak test it works only one time
- From the second time a get this error
    
    ```bash
    (env) pi@raspberrypi4:~/Desktop/Smart-Apple $ python test-ble.py
    Traceback (most recent call last):
      File "/home/pi/Desktop/Smart-Apple/test-ble.py", line 42, in <module>
        asyncio.run(run(address))
      File "/usr/lib/python3.9/asyncio/runners.py", line 44, in run
        return loop.run_until_complete(main)
      File "/usr/lib/python3.9/asyncio/base_events.py", line 642, in run_until_complete
        return future.result()
      File "/home/pi/Desktop/Smart-Apple/test-ble.py", line 36, in run
        async with BleakClient(address) as client:
      File "/home/pi/Desktop/Smart-Apple/env/lib/python3.9/site-packages/bleak/__init__.py", line 565, in __aenter__
        await self.connect()
      File "/home/pi/Desktop/Smart-Apple/env/lib/python3.9/site-packages/bleak/__init__.py", line 605, in connect
        return await self._backend.connect(**kwargs)
      File "/home/pi/Desktop/Smart-Apple/env/lib/python3.9/site-packages/bleak/backends/bluezdbus/client.py", line 249, in connect
        assert_reply(reply)
      File "/home/pi/Desktop/Smart-Apple/env/lib/python3.9/site-packages/bleak/backends/bluezdbus/utils.py", line 22, in assert_reply
        raise BleakDBusError(reply.error_name, reply.body)
    bleak.exc.BleakDBusError: [org.bluez.Error.Failed] Software caused connection abort
    ```
    
- if I create a new virtual environment and run the script it works the first time and then stops working the following times
- I tried removing the /var/lib/bluetooth directory but without success
- Reinstalling bleak didnt work
    
    #### **Solution**

    Installing bluepy with libglib fixes the dependencies
        
    ```bash
    sudo apt-get install libglib2.0-dev
    sudo pip install bluepy
    ```
