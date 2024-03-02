#include "Nicla_System.h"
#include "Arduino_BHY2.h"
#include <ArduinoBLE.h>

#define PACKET_SIZE 130  // Define the maximum BLE packet size
#define BLE_SENSE_UUID(val) ("19b10000-" val "-537e-4f6c-d104768a1214")
#define SERIAL_DEBUG 1
#define TEST_SAMPLE_RATE 0
#define TEST_BLE_RATE 0

const int VERSION = 0x00000000;
int batteryLevel = 0;
// store led state in a char
char ledState[10] = "off";
// program status received from the web app
byte programStatus = 0;

uint32_t packet_id = 0;  // Initialize id for redundancy check
bool startSaving = 1;

// BLE service
BLEService service(BLE_SENSE_UUID("0000"));
// characteristic to send the version of the firmware
BLEUnsignedIntCharacteristic versionCharacteristic(BLE_SENSE_UUID("1001"), BLERead);
// characteristic to send the sensor data to the device
BLECharacteristic dataCharacteristic(BLE_SENSE_UUID("A001"), BLERead | BLENotify, PACKET_SIZE); // One characteristic for all data
// characteristic to send the command to the device
BLECharacteristic commandCharacteristic(BLE_SENSE_UUID("8002"), BLERead | BLEWrite, 1 * sizeof(byte)); // Array of 1 byte, command

// Set BLE refresh rate
unsigned long bleLastUpdateTime = 0; // Store the last update time
unsigned long bleRefreshRate = 30; // rate in Hz
unsigned long bleRefreshTime = (1.0 / bleRefreshRate) * 1000;

Sensor temperature(SENSOR_ID_TEMP);
Sensor humidity(SENSOR_ID_HUM);
Sensor pressure(SENSOR_ID_BARO);
Sensor gas(SENSOR_ID_GAS);
SensorXYZ gyroscope(SENSOR_ID_GYRO);
SensorXYZ accelerometer(SENSOR_ID_ACC);
SensorXYZ gravity(SENSOR_ID_GRA);
SensorQuaternion quaternion(SENSOR_ID_RV);
SensorBSEC bsec(SENSOR_ID_BSEC);

SensorConfig cfg;

// String to calculate the local and device name
String name;

// Variables to dynamically set sensor sampling rate
unsigned long lastUpdateTime = 0; // Store the last update time
float currentSampleRate = 400.0; // Initial sample rate in Hz
unsigned long sampleRefreshTime = 5000; // Time in ms
bool initialRate = true;


void setup() {
  if (SERIAL_DEBUG){
    Serial.begin(115200);
    Serial.println("Start");
    }

  nicla::begin();
  nicla::leds.begin();
  nicla::enableCharging(100);

  // accelerometer.configure(currentSamplerate, 1);

  //Sensors initialization
  BHY2.begin(NICLA_STANDALONE);
  temperature.begin();
  humidity.begin();
  pressure.begin();
  gyroscope.begin(currentSampleRate, 1);
  accelerometer.begin(currentSampleRate, 1);
  gravity.begin(currentSampleRate, 1);
  quaternion.begin(currentSampleRate, 1);
  bsec.begin();
  gas.begin();

  cfg = accelerometer.getConfiguration();
  Serial.println(String("acceleration configuration - rate: ") + cfg.sample_rate + String("Hz - latency: ") + cfg.latency + String("ms - range: ") + cfg.range);
  

  if (!BLE.begin()){
    if (SERIAL_DEBUG) Serial.println("Failed to initialized BLE!");

    while (1)
      ;
  }

  String address = BLE.address();
  if (SERIAL_DEBUG){
    Serial.print("address = ");
    Serial.println(address);
  }

  address.toUpperCase();

  name = "SmartApple-";
  name += address[address.length() - 5];
  name += address[address.length() - 4];
  name += address[address.length() - 2];
  name += address[address.length() - 1];

  if (SERIAL_DEBUG){
    Serial.print("name = ");
    Serial.println(name);
  }

  BLE.setLocalName(name.c_str());
  BLE.setDeviceName(name.c_str());
  BLE.setAdvertisedService(service);

  // Set advertisement interval (in units of 0.625 ms; 32 * 0.625 ms = 20 ms)
  // BLE.setAdvertisingInterval(32);

  // Add characteristics to service
  service.addCharacteristic(versionCharacteristic);
  service.addCharacteristic(dataCharacteristic);
  service.addCharacteristic(commandCharacteristic);
  // Event handler
  BLE.setEventHandler(BLEDisconnected, blePeripheralDisconnectHandler);
  commandCharacteristic.setEventHandler(BLEWritten, onCommandCharacteristicWrite);
  
  versionCharacteristic.setValue(VERSION);
  BLE.addService(service);
  BLE.advertise();
}

void loop() {

  if (BLE.connected()){

    // if programStatus is 1, start the sensors
    if (programStatus == 1){
      if (!startSaving){
        packet_id = 0;
        startSaving = 1;
      } 

      unsigned long currentTime = millis();

      if (TEST_SAMPLE_RATE){
        if (currentTime - lastUpdateTime >= sampleRefreshTime) { // Check if 5 seconds have passed
          if (!initialRate){
            currentSampleRate = max(currentSampleRate / 2.0, 15.0); // Halve the sample rate, but not below 15Hz

            // Update the accelerometer configuration
            gyroscope.configure(currentSampleRate, 1);
            accelerometer.configure(currentSampleRate, 1);
            quaternion.configure(currentSampleRate, 1);
          }
          cfg = accelerometer.getConfiguration();
          Serial.println(String("Updated sample rate to: ") + cfg.sample_rate + "Hz");
          initialRate = false;

          lastUpdateTime = currentTime; // Reset the last update time
        }
      }
      else if (TEST_BLE_RATE){
        if (currentTime - lastUpdateTime >= sampleRefreshTime) { // Check if 5 seconds have passed
          if (!initialRate){

            // add 5 Hz to the ble communication
            bleRefreshRate+=5;
            bleRefreshRate = constrain(bleRefreshRate, 1, 30);
            bleRefreshTime = (1.0 / bleRefreshRate) * 1000;
          }
          initialRate = false;
          lastUpdateTime = currentTime; // Reset the last update time
        }
      }


      BHY2.update();
      if (dataCharacteristic.subscribed()){
        if (currentTime - bleLastUpdateTime >= bleRefreshTime){
          float gyroValues[3] = {gyroscope.x(), gyroscope.y(), gyroscope.z()};
          float accelValues[3] = {accelerometer.x()-gravity.x(), accelerometer.y()-gravity.y(), accelerometer.z()-gravity.z()};
          float quatValues[4] = {quaternion.x(), quaternion.y(), quaternion.z(), quaternion.w()};
        
          char dataPacket[PACKET_SIZE];
          snprintf(dataPacket, sizeof(dataPacket),
                  "%d,G:%.2f,%.2f,%.2f,A:%.2f,%.2f,%.2f,Q:%.2f,%.2f,%.2f,%.2f",
                  packet_id, gyroValues[0], gyroValues[1], gyroValues[2],
                  accelValues[0], accelValues[1], accelValues[2],
                  quatValues[0], quatValues[1], quatValues[2], quatValues[3]);
          dataCharacteristic.writeValue(dataPacket);
          
          packet_id++;

          bleLastUpdateTime = currentTime;
        }
      }
      if (strcpy(ledState, "green") != 0){
        nicla::leds.setColor(green);
        strcpy(ledState, "green");
      }
    }
    else if (programStatus == 0){
      // if programStatus is 0, set blue led
      if (strcpy(ledState, "blue") != 0){
        nicla::leds.setColor(blue);
        strcpy(ledState, "blue");
      }
      packet_id = 0;
    }
  }
  else{
    // If not connected, start advertising
    BLE.advertise();
    
    // if programStatus is 1, save the data to nvram
    if (programStatus == 1){
      if (startSaving){
        packet_id = 0;
        startSaving = 0;
      }
      // nicla::saveDataToNvram();
      if (SERIAL_DEBUG) Serial.println("Saving data to nvram");
    }
    // if programStatus is 0, reset the packet_id counter
    else{
      packet_id = 0;
    }

    if (strcpy(ledState, "red") != 0){
      nicla::leds.setColor(red);
      strcpy(ledState, "red");
    }

  }
}

void blePeripheralDisconnectHandler(BLEDevice central){
  // Define flashing colors; here: red, blue
  byte colors[2][3] = {
    {255, 0, 0},  // Red
    {0, 0, 255}   // Blue
  };
  
  // Flashing sequence upon disconnection
  for (int i = 0; i < 2; i++) {  // Loop through the color array
    nicla::leds.setColor(colors[i][0], colors[i][1], colors[i][2]); // Set color from array
    delay(20); // Delay for 20 milliseconds
  }
}

void onCommandCharacteristicWrite(BLEDevice central, BLECharacteristic characteristic){
  programStatus = commandCharacteristic.value()[0];

  if (programStatus == 0){
    if (SERIAL_DEBUG) Serial.print("programStatus = 0");
  }
  else if (programStatus == 1){
    if (SERIAL_DEBUG) Serial.print("programStatus = 1");
  }
  else{
    if (SERIAL_DEBUG) Serial.print("programStatus = Unknown");
  }
}