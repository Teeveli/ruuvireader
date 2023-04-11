###--------------------------------------------------------------------------
### Ruuvitag reader v1.0
### Teemu Velin
###
### Example of the sensor data
### data[0] = "XX:XX:XX:XX:XX:XX"
### data[1] {'data_format': 5, 'humidity': 31.29, 'temperature': 20.8, 'pressure': 1028.03, 'acceleration': 984.6014422089783, 'acceleration_x': -28, 'acceleration_y': 20, 'acceleration_z': 984, 'tx_power': 4, 'battery': 2827, 'movement_counter': 2, 'measurement_sequence_number': 303, 'mac': 'cedbfbf80509'}
###
###--------------------------------------------------------------------------


## ------------------------
## User definable variables

configurationFile = ".ruuvi_config" # Location of configuration file where IE: credentials are stored.
dataUpdateInterval = 900 # In seconds. Determines how often acquired new data is stored to database. 900 = 15min
consoleLogging = False # Enables or Disables DEBUG logging to console.
filelogging = False # Enables or Disables sensor data logging to file.

##-------------------------


### -------------------
### MAIN PROGRAM STARTS


## Imports

from ruuvitag_sensor.ruuvi import RuuviTagSensor
from ruuvitag_sensor.log import log
import logging
import time
from threading import Thread
import re
from datetime import datetime
from influxdb import InfluxDBClient


## Global variables

dictTagData = {} # Main dictionary for temporarily storing received tag data.
dictPrevSequence = {} # Dictionary for storing measurement_sequence_number for comparing if the data is actually new we try to write.


## Read configuration file.
configsHandle = open(configurationFile, "r")
configsData = configsHandle.read()
configsHandle.close()

## Assign the data to variables
user = re.search('username="(.*)"', configsData).group(1)
password = re.search('password="(.*)"', configsData).group(1)
database = re.search('database="(.*)"', configsData).group(1)
host = re.search('server="(.*)"', configsData).group(1)
port = re.search('port="(.*)"', configsData).group(1)
logfile = re.search('logfile="(.*)"', configsData).group(1)
dataUpdateInterval = re.search('update_interval="(.*)"', configsData).group(1)
filelogging = re.search('log_enabled="(.*)"', configsData).group(1)


#LOG
if filelogging == True:
	logfile = open(logfile, "a")
	logfile.write("--------------------------------\n")
	logfile.write("Program started: " + str(datetime.utcnow()) + "\n")
	logfile.flush()

# Enable ruuvi internal logging
for handler in log.handlers:
    if isinstance(handler, logging.FileHandler):
        handler.setLevel(logging.DEBUG)

## Open Influx connection

influxdbClient = InfluxDBClient(host=host, port=port, username=user, password=password, database=database)


## Function that parses the data sensors send

def ruuvi_data(data):
	
	# If the MAC-address of the sensor is already in the data dictionary and its reading is new, update the data to dictTagData.
	# If the sensor's MAC-address is new, we write its data to dictTagData and update dictPrevSequence so we know the data is fresh.
	if data[0] in dictTagData:
		if data[1]["measurement_sequence_number"] != dictPrevSequence[data[0]]:
			dictTagData.update({data[0]:data[1]})
	else:
		dictTagData.update({data[0]:data[1]})
		dictPrevSequence.update({data[0]:data[1]["measurement_sequence_number"]})

		# DEBUG: Print the sensor found as new sensor.
		if consoleLogging == True: print("New sensor found: " + data[0])

		# LOG
		if filelogging == True:
			logfile.write("New sensor found: " + data[0] + "\n")
			logfile.flush()


## Function that inserts the data to database

def db_insert():

	# Declare the data list.
	allvaluedata = []
	
	# Infinite loop that pushes NEW data to database based on given time interval in dataUpdateInterval
	# It checks if the data in the dictTagData has newer measurement_sequence_number than the previous write, and if so, writes the data to database.
	# This is to prevent pushing same data to database, in case the sensor dies or has bad reception.

	while True:
		time.sleep(int(dataUpdateInterval))
		# LOG
		if filelogging == True:
			logfile.write(str(datetime.utcnow()) + "\n")
		for measurements in dictTagData:
			# LOG
			if filelogging == True:
				logfile.write("Sensor: " + str(measurements) + " - sensorsequence " + str(dictTagData[measurements]["measurement_sequence_number"]) + " : " + str(dictPrevSequence[measurements]) + " prevsequence" + "\n")
				logfile.flush()
			
			# If the data measurement_sequence_number is changed, insert values to dict
			if dictTagData[measurements]["measurement_sequence_number"] != dictPrevSequence[measurements]:
				valuedata = ("{mac} humidity={humidity},temperature={temperature},pressure={pressure},battery={battery} {timestamp}"
							.format(mac=measurements,
									humidity=dictTagData[measurements]["humidity"],
									temperature=dictTagData[measurements]["temperature"],
									pressure=dictTagData[measurements]["pressure"],
									battery=dictTagData[measurements]["battery"],
									timestamp=int(time.time() * 1000)))
				allvaluedata.append(valuedata)

				# Update current measurement number to compare against next round			
				dictPrevSequence[measurements] = dictTagData[measurements]["measurement_sequence_number"]

		# Push the data to database
		influxdbClient.write_points(allvaluedata, database=database, time_precision='ms', protocol='line')

		# LOG
		if filelogging == True:
			logfile.write("DATA WRITTEN TO DB: " + str(allvaluedata) + "\n")
			logfile.flush()

		# DEBUG: Print the amount of rows inserted and their data.
		if consoleLogging == True:
			print(allvaluedata ,"\n")


		# Clear the data list after insertion.
		valuedata = []
		allvaluedata = []



### Start the thread for database insert.

t1 = Thread(target = db_insert)
t1.start()


# Start the main worker that listens for the tags and sends the data to ruuvi_data function
RuuviTagSensor.get_data(ruuvi_data)
