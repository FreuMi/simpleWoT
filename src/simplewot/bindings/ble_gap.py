import asyncio
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

# Global lock to prevent concurrent BlueZ scan operations
scan_lock = asyncio.Lock()

async def listen(forms) -> bytes | None:
    # MAC is in gap everything behind ://
    target_mac = forms["target"].split("://")[1].replace("-",":")

    raw_bytes = await get_gap_advertisement(target_mac)

    return raw_bytes


async def get_gap_advertisement(target_mac: str) -> bytes | None:
    # Create an event flag
    found_event = asyncio.Event()
    TIME_OUT = 20.0 # Scan time out to 20s
    value = None

    # Define the callback
    def read_once_callback(device: BLEDevice, adv_data: AdvertisementData) -> None:
        nonlocal value 
        
        if device.address.lower() != target_mac.lower():
            return
        
        if not adv_data.manufacturer_data:
            return
        
        for company_id, raw_bytes in adv_data.manufacturer_data.items():                    
            # Store the hex payload in the outer variable
            value = raw_bytes
            break 
                
        found_event.set()
    
    async with scan_lock:
        scanner = BleakScanner(detection_callback=read_once_callback)

        try:
            await scanner.start()
            try:
                await asyncio.wait_for(found_event.wait(), timeout=TIME_OUT)
            except asyncio.TimeoutError:
                print(f"Timeout: Did not hear from {target_mac} within {TIME_OUT} seconds.")
            except asyncio.CancelledError:
                # request was cancelled from outside (e.g. HTTP timeout)
                raise
        finally:
            # Short delay to finish any D-Bus operations
            await asyncio.sleep(0.1)
            try:
                await asyncio.shield(scanner.stop())
            except Exception as e:
                print(f"scanner.stop() failed: {e}")

        return value