#include "Nicla_System.h"
#include "Arduino_BHY2.h"
#include <ArduinoBLE.h>

#define PACKET_SIZE 130  // Define the maximum BLE packet size
#define BLE_SENSE_UUID(val) ("19b10000-" val "-537e-4f6c-d104768a1214")
#define SERIAL_DEBUG 1

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

// RSSI
int rssi = 0;
int pastRssi = 0;
// update the rssi every x seconds
unsigned long lastRssiUpdate = 0;
unsigned long refreshRateRssi = 2000;

Sensor temperature(SENSOR_ID_TEMP);
Sensor humidity(SENSOR_ID_HUM);
Sensor pressure(SENSOR_ID_BARO);
Sensor gas(SENSOR_ID_GAS);
SensorXYZ gyroscope(SENSOR_ID_GYRO);
SensorXYZ accelerometer(SENSOR_ID_ACC);
SensorQuaternion quaternion(SENSOR_ID_RV);
SensorBSEC bsec(SENSOR_ID_BSEC);

// String to calculate the local and device name
String name;

void setup() {
  if (SERIAL_DEBUG){
    Serial.begin(115200);
    Serial.println("Start");
  }

  nicla::begin();
  nicla::leds.begin();
  nicla::enableCharging(100);

  //Sensors initialization
  BHY2.begin(NICLA_STANDALONE);
  temperature.begin();
  humidity.begin();
  pressure.begin();
  gyroscope.begin();
  accelerometer.begin();
  quaternion.begin();
  bsec.begin();
  gas.begin();

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

      BHY2.update();
      if (dataCharacteristic.subscribed()){

        float gyroValues[3] = {gyroscope.x(), gyroscope.y(), gyroscope.z()};
        float accelValues[3] = {accelerometer.x(), accelerometer.y(), accelerometer.z()};
        float quatValues[4] = {quaternion.x(), quaternion.y(), quaternion.z(), quaternion.w()};
        
        if (millis() - lastRssiUpdate > refreshRateRssi){
          rssi = BLE.rssi();
          // if it is different from 0, update the pastRssi
          if (rssi != 0){
            pastRssi = rssi;
          }
          // if it is 0, use the pastRssi
          else{
            rssi = pastRssi;
          }
          lastRssiUpdate = millis();
        }

        char dataPacket[PACKET_SIZE];
        snprintf(dataPacket, sizeof(dataPacket),
                "%d,%d,G:%.2f,%.2f,%.2f,A:%.2f,%.2f,%.2f,Q:%.2f,%.2f,%.2f,%.2f",
                packet_id, rssi, gyroValues[0], gyroValues[1], gyroValues[2],
                accelValues[0], accelValues[1], accelValues[2],
                quatValues[0], quatValues[1], quatValues[2], quatValues[3]);
        dataCharacteristic.writeValue(dataPacket);
        
        packet_id++;
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
    pastRssi = 0;
    
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