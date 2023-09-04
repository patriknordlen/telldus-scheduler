# telldus-scheduler

A simple utility for scheduling events for devices connected to the Telldus Live! service.

## Installation

1. Clone this repository
2. Run `pip install -r requirements.txt`

## Configuration

telldus-scheduler expects a configuration file using the following format:

```
auth:
  client_key: <client_key>
  client_secret: <client_secret>
  resource_owner_key: `resource_owner_key`
  resource_owner_secret: `resource_owner_secret`
coordinates:
  latitude: <latitude_in_decimal_format>
  longitude: <longitude_in_decimal_format>
events:
  - name: <event_name>
    action: <"on"|"off">
    at: <"sunset"|"sunrise"|"HH:MM">
    devices:
      - <device1>
      - <device2>
      - ...
  - ...
```

You can generate the required credentials for interacting with the Telldus Live API [here](https://api.telldus.com/keys/index).

## Running

```
▶ python3 telldus-scheduler.py -h
usage: telldus-scheduler.py [-h] [-c CONFIG] [-d] [-l] [-v]

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Config file to load
  -d, --daemon          Run as daemon (log to syslog)
  -l, --list-devices    List registered devices and exit
  -v, --verbose         Verbose output, show all debug messages
```