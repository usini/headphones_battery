import asyncio
from bleak import BleakScanner

async def scan_devices():
    async with BleakScanner() as scanner:
        devices = await scanner.discover()
        for d in devices:
            print(d)
            print(f"Name: {d.name}, MAC: {d.address}")

loop = asyncio.get_event_loop()
while True:
    loop.run_until_complete(scan_devices())