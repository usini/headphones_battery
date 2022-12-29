import asyncio
import threading
import time
import asyncio
from bleak import BleakClient

class BatteryLevel:
    def __init__(self, widget):
        self.device_not_founded_counter = 0

        self.widget = widget

        self.thread = threading.Thread(target=self.update_battery_level)
        self.thread.start()

    async def get_battery_level(self):
        async with BleakClient(self.widget.settings.get["headphones_mac"]) as client:
            battery_level = int.from_bytes(await client.read_gatt_char(self.widget.settings.get["headphones_battery_uuid_charateristic"]), "little")
            print(battery_level)
            self.widget.label["battery_text"].config(text=f"{battery_level}%")
            if(battery_level <= 5):
                self.widget.label["battery_icon"].config(image=self.widget.images["battery"]["0"])
            elif(battery_level <= 10):
                self.widget.label["battery_icon"].config(image=self.widget.images["battery"]["10"])
            elif(battery_level <= 25):
                self.widget.label["battery_icon"].config(image=self.widget.images["battery"]["25"])
            elif(battery_level <= 50):
                self.widget.label["battery_icon"].config(image=self.widget.images["battery"]["50"])
            elif(battery_level <= 75):
                self.widget.label["battery_icon"].config(image=self.widget.images["battery"]["75"])
            elif(battery_level >= 75):
                self.widget.label["battery_icon"].config(image=self.widget.images["battery"]["100"])

    def update_battery_level(self):
            while True:
                print("Getting battery level")
                try:
                    asyncio.run(self.get_battery_level())
                    retry = 300
                    self.device_not_founded_counter = 0
                    print("Success, retry in 5 minutes")
                    self.widget.tooltip["text"] = self.widget._["Connected"]
                    self.widget.tray_icon_update()
                except Exception as e:
                    print("Failed to get informations, retry in 1 second")
                    print(str(e))
                    if "Access Denied" in str(e):
                        print("Access denied to battery level")
                        self.widget.tooltip["text"] = self.wdiget._["Access denied"]
                        self.widget.tray_icon_update()
                        retry = 1
                        self.device_not_founded_counter = 0
                    elif "not found." in str(e):
                        print("Headphones not founded")
                        self.widget.tooltip["text"] = self.widget._["Disconnected"]
                        self.widget.tray_icon_update()
                        self.device_not_founded_counter = self.device_not_founded_counter + 1
                        print(self.device_not_founded_counter)
                        if(self.device_not_founded_counter == 10):
                            retry = 300
                            print("Headphones not connected, retry in 5 minutes")
                            self.widget.tooltip["text"] = self.widget._["Déconnecté"]
                            self.widget.tray_icon_update()
                        else:
                            retry = 1
                    else:
                        print("Erreur inconnu")
                        self.widget.tooltip["text"] = self.widget._["Unknown"]
                        self.widget.tray_icon_update()
                        retry = 1

                print("Waiting...")
                time.sleep(retry) # attend 5 minutes avant de relancer la fonction
