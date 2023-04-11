# Ruuvitag - InfluxDB writer

Python script for gathering and pushing data from RuuviTag sensors to InfluxDB with Raspberry PI

This code is released as is, without any promises of bug fixing. Its built solely for my own use.

## Requirements

These must be installed in Raspberry PI
* python3
* ruuvitag_sensor Python library
* influxdb Python library

Database server
* InfluxDB
* Database with user having write and read rights to it

## Installation

* Fill the correct information in `.ruuvi_config` file. The configuration is read from the home directory of user starting the script
* Place bash script and python script inside `/usr/local/bin` and make sure they have the right permissions for your user
* `ruuvireader` bash script can be inserted to crontab to provide automatic start of the script at boot. It creates an screen session which has the python script running. IE: `@reboot USERNAME /usr/local/bin/ruuvireader`
