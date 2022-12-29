import os
import json
from screeninfo import get_monitors, Enumerator
import sys
import os
import msvcrt

class Settings:
    def __init__(self):
        """Initialize the `get` dictionary with default values for window position and screen size"""
        self.check_is_running()
        self.get = {
            "win_x":10,
            "win_y":10,
            "width": 0,
            "height": 0,
            "headphones_mac": "00:00:00:00:00:00",
            "headphones_battery_uuid_charateristic" :"00000000-0000-0000-0000-000000000000"
        }
        self.get_screens_size()

    def check_is_running(self):
        print("Check if application is running")
        try:
            print(" Opening lock")
            self.fd = open("lock", 'w')
            print("Checking lock")
            msvcrt.locking(self.fd.fileno(), msvcrt.LK_RLCK, 1)
        except IOError:
            print("Application is already running")
            os._exit(1)

    def write(self):
        """Save the `get` dictionary to a file"""
        print("Saving")
        with open('settings/config.json', 'w') as config_file:
            json.dump(self.get, config_file)

    def read(self):
        """Load the `get` dictionary from a file"""
        print("Loading")
        if not os.path.exists('settings/config.json'):
            self.write()
        else:
            with open('settings/config.json', 'r') as config_file:
                try:
                    temp_config = json.load(config_file)
                    if(temp_config["win_x"] > temp_config["width"]):
                        print("Window is offscreen (X)")
                        temp_config["win_x"] = 10
                    if(temp_config["win_y"] > temp_config["height"]):
                        print("Window is offscreen (Y)")
                        temp_config["win_y"] = 10
                    print(temp_config["headphones_mac"])
                    print(temp_config["headphones_battery_uuid_charateristic"])
                    self.get = temp_config
                except:
                    print("Corrupted configuration file")
                    self.write()

    def load(self):
        """Load the `get` dictionary from a file if it exists, otherwise create a new one"""
        if (os.path.exists("settings/config.json")):
            print("Configuration file exists")
            self.read()
        else:
            print("Creating configuration file")
            self.write()
        self.print()

    def print(self):
        """Print the contents of the `get` dictionary"""
        print(self.get)

    def get_screens_size(self):
        """Get the total size of all screens and update the `get` dictionary"""
        for m in get_monitors(Enumerator.Windows):
            self.get["width"] = self.get["width"] + m.width
            self.get["height"] = self.get["height"] + m.height
        print("Screen size: " + str(self.get["width"]) + "x" + str(self.get["height"]))
