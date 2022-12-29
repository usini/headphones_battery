
import threading
import time

from settings import Settings
from widget import Widget
from battery_level import BatteryLevel
settings = Settings()
settings.load()

widget = Widget(settings)
battery_level = BatteryLevel(widget)

widget.start()


