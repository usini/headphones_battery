import tkinter as tk
import tkinter.messagebox
from tkinter import ttk
import threading
import time
from functools import partial
import os
import re
import asyncio
from bleak import BleakScanner
from bleak import BleakClient
import pystray
from PIL import Image
import locale
import os
import json

class Widget:

    def __init__(self, settings):
        self.settings = settings
        
        self.language = locale.getdefaultlocale()[0]
        self._ = {}
        if "_" in self.language:
            self.language = self.language.split("_")[0]
        print("System Language: " + str(self.language))
        
        if os.path.exists("settings/i18n/" + self.language + ".json"):
            with open("settings/i18n/" + self.language + ".json", "r", encoding="utf-8") as f:
                print("Translation found")
                self._ = json.load(f)
        else:
            print("Translation not found, default to english")
            with open("settings/i18n/en.json", encoding="utf-8") as f:
                self._ = json.load(f)
                    
        self.root = tk.Tk()
        self.root.title(self._["Headphones Battery"])
        self.root.attributes("-topmost", True)
        self.root.geometry("150x24+"+str(settings.get['win_x'])+"+"+str(settings.get['win_y']))

        self.x_offset = None
        self.x_offset = None

        self.running = True

        self.tooltip = {
            "label": None,
            "text": self._["Connection"],
            "displayed": False,
            "thread": None
        }

        self.isfocus = True

        self.images = {}
        self.load_images()

        self.labels = {}
        self.load_labels()

        self.thread_lift = threading.Thread(target=self.force_lift)
        self.thread_lift.start()

        self.root.bind("<FocusIn>", partial(self.on_focus_in, self))
        self.root.bind("<FocusOut>", partial(self.on_focus_out, self))

        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label=self._["Find my headphones"], command=partial(self.open_scan_window, self))
        self.context_menu.add_command(label=self._["Settings"], command=partial(self.open_config_window, self))
        self.context_menu.add_command(label=self._["Close"], command=partial(self.exit_callback, self))

        self.root.bind("<Button-3>", partial(self.show_context_menu, self))

        self.root.configure(background="#222222")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-transparentcolor", '#222222')
        self.root.bind("<ButtonPress-1>", partial(self.on_widget_press,self))
        self.root.bind("<B1-Motion>", partial(self.on_widget_move,self))
        self.root.bind("<ButtonRelease-1>", partial(self.on_widget_release,self))

        self.tray_image = image = Image.open("images/png/icon.png")
        self.tray_menu = pystray.Menu(
            pystray.MenuItem(self._["Show"], partial(self.force_lift_widget, self)),
            pystray.MenuItem(self._["Reset Widget Position"], partial(self.change_position, self)),
            pystray.MenuItem(self._["Close"], partial(self.on_quit_clicked, self))
            )
        self.tray_icon = pystray.Icon(self._["Headphones Battery"], icon=self.tray_image , menu=self.tray_menu)
        self.tray_icon.title = self.tooltip["text"]
        self.tray_icon.run_detached()

    def tray_icon_update(self):
        self.tray_icon.title = self.tooltip["text"]

    def on_quit_clicked(self, instance, icon, item):
        self.running = False
        self.settings.fd.close()
        os._exit(0)
 
    def change_position(self, instance, icon, item):
        self.root.geometry("+10+10")
        print("Saving position")
        self.settings.get["win_x"] = self.root.winfo_x()
        self.settings.get["win_y"] = self.root.winfo_y()
        self.settings.write()

    def start(self):
        #self.open_config_window(self)
        #self.open_scan_window(self)
        print("Starting Widget - ")
        self.root.mainloop()

    def load_labels(self):
        self.label = {
            "headphones_icon": tk.Label(self.root, image=self.images["headphones"], background="#222222"),
            "battery_icon": tk.Label(self.root, image=self.images["battery"]["unknown"], background="#222222"),
            "battery_text": tk.Label(self.root, text="?%", foreground="white", background="#222222", font="16px")
        } 

        self.label["headphones_icon"].pack(side=tk.LEFT, anchor=tk.N)
        self.label["battery_icon"].pack(side=tk.LEFT, anchor=tk.N)
        self.label["battery_icon"].bind("<ButtonPress-1>", partial(self.show_tooltip, self))
        self.label["battery_text"].pack(side=tk.LEFT, anchor=tk.N)

    def load_images(self):
        self.images = {
            "headphones": tk.PhotoImage(file="images/png/headphones.png"),
            "battery": {
                "unknown":tk.PhotoImage(file="images/png/battery_unknown.png"),
                "0":tk.PhotoImage(file="images/png/battery_0.png"),
                "10":tk.PhotoImage(file="images/png/battery_10.png"),
                "25":tk.PhotoImage(file="images/png/battery_25.png"),
                "50":tk.PhotoImage(file="images/png/battery_50.png"),
                "75":tk.PhotoImage(file="images/png/battery_75.png"),
                "100":tk.PhotoImage(file="images/png/battery_full.png")
            }
        }

    def force_lift_widget(self, instance, icon, item):
        self.root.lift()

    def force_lift(self):
        while True:
            if self.isfocus is False:
                self.root.lift()
            time.sleep(1)

    def destroy_tooltip(self):
        time.sleep(1)
        print("Destroy tooltip")
        self.tooltip["label"].destroy()
        self.tooltip["displayed"] = False

    def show_tooltip(self, instance, event):
        if self.tooltip["displayed"] is False:
            print("Display tooltip")

            # Créer une étiquette pour afficher le tooltip
            self.tooltip["label"] = tk.Label(self.root, text=self.tooltip["text"], background='white', font=("Helvetica", 10))

            # Placer l'étiquette sur le widget
            self.tooltip["label"].place(x=self.label["battery_text"].winfo_x()-50, y=self.label["battery_text"].winfo_y())
            self.tooltip["displayed"] = True
            self.tooltip["thread"] = threading.Thread(target=self.destroy_tooltip)
            self.tooltip["thread"].start()

    def on_focus_in(self, instance, event):
        self.isfocus = True

    def on_focus_out(self, instance, event):
        self.isfocus = False

    def exit_callback(self, instance):
        self.running = False
        self.settings.fd.close()
        self.root.destroy()
        os._exit(0)

    def show_context_menu(self, instance, event):
        self.context_menu.post(event.x_root, event.y_root)

    def on_widget_press(self, instance, event):
        print("Moving")
        self.x_offset = event.x
        self.y_offset = event.y

    def on_widget_move(self, instance, event):
        x = self.root.winfo_x() - self.x_offset + event.x
        y = self.root.winfo_y() - self.y_offset + event.y
        self.root.geometry("+{0}+{1}".format(x, y))

    def on_widget_release(self, instance, event):
        self.x_offset = None
        self.y_offset = None
        print("Saving position")
        self.settings.get["win_x"] = self.root.winfo_x()
        self.settings.get["win_y"] = self.root.winfo_y()
        self.settings.write()

    def save_config(self, instance):
        mac = self.headphones_mac_entry.get()
        uuid = self.headphones_battery_uuid_entry.get()
        mac_regex = r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
        uuid_regex = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        check_mac = False
        check_uuid = False
        if re.match(mac_regex, mac):
            print(mac)
            check_mac = True
        else:
            print("Invalid MAC Address")
        if re.match(uuid_regex, uuid):
            check_uuid = True
            print(uuid)
        else:
            print("UUID invalide")
        if check_uuid is True and check_mac is True:
            tkinter.messagebox.showinfo(self._["Saving"], self._["MAC Address saved"])
            self.settings.get["headphones_mac"] = mac
            self.settings.get["headphones_battery_uuid_charateristic"] = uuid
            self.settings.write()
            self.config_window.destroy()
        else:
            if check_mac is False:
                tkinter.messagebox.showerror(self._["Error"], self._["Invalid Mac Address"])
            if check_uuid is False:
                tkinter.messagebox.showerror(self._["Error"], self._["Invalid Battery Characteristic"])
            print("Error")

    def start_scan_uuid(self, instance):
        print("Starting UUID Scan")
        self.scan_uuid_button.config(state="disabled")
        scan_uuid_thread = threading.Thread(target=partial(self.scan_uuid,self))
        scan_uuid_thread.start()
    
    def scan_uuid(self, instance):
        asyncio.run(self._scan_uuid())

    async def _scan_uuid(self):
        mac_address = self.values[self.option.current()].split("-")[len(self.values[self.option.current()].split("-")) -1].strip()
        print(mac_address)
        self.values_uuid = []
        async with BleakClient(mac_address) as client:
                for service in client.services:
                    for char in service.characteristics:
                        if "read" in char.properties:
                            try:
                                characteristics = await client.read_gatt_char(char.uuid)
                                print(f"{char.uuid} - {char.description}")
                                
                                self.values_uuid.append(f"{char.uuid} - {char.description}")
                            except:
                                pass
                
                self.option_uuid.config(values=self.values_uuid)
                self.option_uuid.set(self.values_uuid[0])
                self.scan_button.config(state="normal")
                self.scan_uuid_button.config(state="normal")

        self.scan_button.config(state="normal")
        self.scan_uuid_button.config(state="normal")

    def start_scan(self, instance):
        print("Starting scan")
        self.scan_button.config(state="disabled")
        scan_thread = threading.Thread(target=partial(self.scan,self))
        scan_thread.start()
    
    def scan(self, instance):
        asyncio.run(self.scan_devices())

    async def scan_devices(self):
        async with BleakScanner() as scanner:
            devices = await scanner.discover()
            devices_counter = 0
            self.values = []
            for d in devices:
                self.values.append(f"{d.name} - {d.address}")

            self.option.config(values=self.values)
            self.option.set(self.values[0])
            self.scan_button.config(state="normal")
            self.scan_uuid_button.config(state="normal")

    def save_scan(self, instance):
        mac = self.values[self.option.current()].split("-")[len(self.values[self.option.current()].split("-")) -1].strip()
        uuid = self.values_uuid[self.option_uuid.current()].split("-")
        uuid.pop()
        uuid = "-".join(uuid).strip()
        mac_regex = r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
        uuid_regex = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"

        check_mac = False
        check_uuid = False
        if re.match(mac_regex, mac):
            print(mac)
            check_mac = True
        else:
            print("Invalid MAC Address")
        if re.match(uuid_regex, uuid):
            check_uuid = True
            print(uuid)
        else:
            print("UUID invalide")
        if check_uuid is True and check_mac is True:
            tkinter.messagebox.showinfo(self._["Saving"], self._["MAC Address saved"])
            self.settings.get["headphones_mac"] = mac
            self.settings.get["headphones_battery_uuid_charateristic"] = uuid
            self.settings.write()
            self.scan_window.destroy()
        else:
            if check_mac is False:
                tkinter.messagebox.showerror(self._["Error"], self._["Invalid Mac Address"])
            if check_uuid is False:
                tkinter.messagebox.showerror(self._["Error"], self._["Invalid Battery Characteristic"])
            print("Error")


    def open_config_window(self, instance):
        self.config_window = tk.Toplevel(self.root)
        self.config_window.title(self._["Settings"])
        self.config_window.resizable(width=False, height=False)

        self.root.bind("<Button-3>", lambda event: self.context_menu.post(event.x_root, event.y_root))      

        mac = tk.StringVar(value=self.settings.get["headphones_mac"])
        uuid = tk.StringVar(value=self.settings.get["headphones_battery_uuid_charateristic"])

        canvas = tk.Canvas(self.config_window)
        canvas.configure(width=220,height=120)
        canvas.pack(side="left")
        frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=frame, anchor="nw")
        
        headphones_mac_label = tk.Label(frame, text=self._["Headphones MAC Address"] + ":")
        # Créez des widgets Entry et utilisez les variables de chaîne pour stocker les valeurs saisies par l'utilisateur
        self.headphones_mac_entry = tk.Entry(frame, textvariable=mac)

        headphones_battery_uuid_label = tk.Label(frame, text=self._["UUID Battery Characteristic"] + ":")
        self.headphones_battery_uuid_entry = tk.Entry(frame, textvariable=uuid)

        self.headphones_mac_entry.config(width=len(self.headphones_mac_entry.get()))
        self.headphones_battery_uuid_entry.config(width=len(self.headphones_battery_uuid_entry.get()))

        headphones_mac_label.pack()
        self.headphones_mac_entry.pack(expand=True)
        headphones_battery_uuid_label.pack()
        self.headphones_battery_uuid_entry.pack(expand=True)
        # Ajoutez les widgets à la fenêtre de configuration       
    
        button_frame = tk.Frame(frame)
        button_frame.pack(side="bottom", pady=10)
    
        cancel_button = tk.Button(button_frame, text=self._["Cancel"], command=self.config_window.destroy)
        cancel_button.pack(side="left")
        save_button = tk.Button(button_frame, text=self._["Save"], command=partial(self.save_config, self))
        save_button.pack(side="left")

    def open_scan_window(self, instance):
        # Créez la nouvelle fenêtre
        self.scan_window = tk.Toplevel(self.root)
        self.scan_window.title(self._["Scan"])
        self.scan_window.resizable(width=False, height=False)
        # Créez le champ de choix
        self.values = [self._["Bluetooth Scan"]]
        self.option = ttk.Combobox(self.scan_window, values = self.values)
        self.option.set(self._["Bluetooth Scan"])
        self.option.config(width=100)
        self.option.pack(expand=True)

        # Créez un widget Frame pour contenir le bouton "SCAN"
        button_frame = tk.Frame(self.scan_window)
        button_frame.pack(anchor="center")
        # Créez le bouton "SCAN"
        self.scan_button = tk.Button(button_frame, text=self._["Bluetooth Scan"], command=partial(self.start_scan,self))
        self.scan_button.pack()

        self.values_uuid = self._["UUID Scan"]
        self.option_uuid = ttk.Combobox(self.scan_window, values = self.values)
        self.option_uuid.set(self._["UUID Scan"])
        self.option_uuid.config(width=100)
        self.option_uuid.pack(expand=True)

        # Créez un widget Frame pour contenir le bouton "SCAN"
        button_frame2 = tk.Frame(self.scan_window)
        button_frame2.pack(anchor="center")
        self.scan_uuid_button = tk.Button(button_frame2, text=self._["UUID Scan"], command=partial(self.start_scan_uuid,self))
        self.scan_uuid_button.pack(side="bottom")
        self.scan_uuid_button.config(state="disabled")
        
        button_frame = tk.Frame(self.scan_window)
        button_frame.pack(side="bottom", pady=10)
    
        cancel_button = tk.Button(button_frame, text=self._["Cancel"], command=self.scan_window.destroy)
        cancel_button.pack(side="left")
        save_button = tk.Button(button_frame, text=self._["Save"], command=partial(self.save_scan, self))
        save_button.pack(side="left")



