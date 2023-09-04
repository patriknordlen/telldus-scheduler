#!/usr/bin/env python

import sys
import time
from argparse import ArgumentParser

import daemon
import logging
import logging.handlers
import schedule
import yaml
from prettytable import PrettyTable
from requests_oauthlib import OAuth1Session
from suntime import Sun


class TelldusClient:
    def __init__(
        self, client_key, client_secret, resource_owner_key, resource_owner_secret
    ):
        self.client = OAuth1Session(
            client_key=client_key,
            client_secret=client_secret,
            resource_owner_key=resource_owner_key,
            resource_owner_secret=resource_owner_secret,
        )
        self.base_url = "https://api.telldus.com/json"

    def get(self, endpoint, *args, **kwargs):
        return self.client.get(url=f"{self.base_url}{endpoint}", *args, **kwargs)

    def post(self, endpoint, *args, **kwargs):
        return self.client.post(url=f"{self.base_url}{endpoint}", *args, **kwargs)

    def on(self, devices):
        for device in devices:
            self.get("/device/turnOn", params={"id": device})

    def off(self, devices):
        for device in devices:
            self.get("/device/turnOff", params={"id": device})

    def list_devices(self):
        return self.get("/devices/list").json()


def read_config(config_file):
    with open(config_file) as f:
        config = yaml.safe_load(f)
        for section in ["auth", "coordinates", "events"]:
            if section not in config:
                raise TypeError(f"missing '{section}' section")
        for auth_key in [
            "client_key",
            "client_secret",
            "resource_owner_key",
            "resource_owner_secret",
        ]:
            if auth_key not in config["auth"]:
                raise TypeError(f"missing key '{auth_key}' in auth section")
        for coord_key in ["latitude", "longitude"]:
            if coord_key not in config["coordinates"]:
                raise TypeError(f"missing key '{coord_key}' in coordinates section")

    return config


def run_event(event, t):
    logging.info(f"Executing event: {event}")
    if event["action"] == "on":
        func = t.turnOnLights
    elif event["action"] == "off":
        func = t.turnOffLights

    func(event["devices"])


def print_device_list(t):
    devices = sorted(t.list_devices()["device"], key=lambda x: x["clientName"])
    tbl = PrettyTable(["Location", "Name", "ID"])
    tbl.align = "l"
    for device in devices:
        tbl.add_row([device["clientName"], device["name"], device["id"]])

    print(tbl)


def run_scheduler(t, config):
    sun = Sun(config["coordinates"]["latitude"], config["coordinates"]["longitude"])

    for event in config["events"]:
        if event["at"] == "sunset":
            event_time = sun.get_local_sunset_time().strftime("%H:%M")
        elif event["at"] == "sunrise":
            event_time = sun.get_local_sunrise_time().strftime("%H:%M")
        else:
            event_time = event["at"]
        logging.info(f"Scheduling event: {event}")
        schedule.every().day.at(event_time).do(run_event, event, t)

    while True:
        schedule.run_pending()
        time.sleep(1)


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "-c", "--config", help="Config file to load", default="config.yaml"
    )
    parser.add_argument(
        "-d", "--daemon", help="Run as daemon (log to syslog)", action="store_true", default=False
    )
    parser.add_argument("-l", "--list-devices", help="List registered devices and exit", action="store_true", default=False)
    parser.add_argument("-v", "--verbose", help="Verbose output, show all debug messages", action="store_true", default=False)
    args = parser.parse_args()

    logging.basicConfig(
        handlers=[
            logging.handlers.SysLogHandler(address="/dev/log")
            if args.daemon
            else logging.StreamHandler(sys.stdout)
        ],
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        config = read_config(args.config)
    except Exception as e:
        sys.stderr.write(f"ERROR: {e}")
        sys.exit(1)

    t = TelldusClient(
        config["auth"]["client_key"],
        config["auth"]["client_secret"],
        config["auth"]["resource_owner_key"],
        config["auth"]["resource_owner_secret"],
    )

    if args.list_devices:
        print_device_list(t)
        sys.exit(0)
    else:
        if args.daemon:
            with daemon.DaemonContext():
                run_scheduler(t, config)
        else:
            run_scheduler(t, config)


if __name__ == "__main__":
    main()
