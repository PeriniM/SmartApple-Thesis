from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from decouple import config

# InfluxDB Settings
INFLUXDB_URL = config('INFLUXDB_URL', cast=str)
INFLUXDB_TOKEN = config('INFLUXDB_TOKEN', cast=str)
INFLUXDB_ORG = config('INFLUXDB_ORG', cast=str)
INFLUXDB_BUCKET = config('INFLUXDB_BUCKET', cast=str)

# Setup InfluxDB client
client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)

# Configure batch write client
write_api = client.write_api(write_options=SYNCHRONOUS)

# Query data from InfluxDB
query1 = '''
from(bucket: "Smart-Apple")
  |> range(start: -1m)
  |> filter(fn: (r) => r["_measurement"] == "nicla")
  |> filter(fn: (r) => r["address"] == "EE:DF:46:E7:08:80" and r["production_line"] == "test")
  |> filter(fn: (r) => r["_field"] == "a_x" or r["_field"] == "a_y" or r["_field"] == "a_z")
'''

# Query data from InfluxDB
query2 = '''
from(bucket: "Smart-Apple")
  |> range(start: -6h)
  |> filter(fn: (r) => r["_measurement"] == "movement_sensor_data")
'''

tables = client.query_api().query(query2, org=INFLUXDB_ORG)

dataframes = []

# Extract relevant information from FluxRecords
for table in tables:
    for record in table.records:
        data = {
            '_time': record['_time'],
            '_value': record['_value'],
            '_field': record['_field'],
        }
        dataframes.append(pd.DataFrame([data]))

# Concatenate DataFrames
df = pd.concat(dataframes)

# Pivot the DataFrame to get columns for each sensor type
df_pivot = df.pivot(index='_time', columns='_field', values='_value')

# Reset index to make '_time' a regular column
df_pivot.reset_index(inplace=True)
# Save to CSV
df_pivot.to_csv('sensor_data.csv', index=False)
