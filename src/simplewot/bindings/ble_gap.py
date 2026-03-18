import asyncio
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

scan_lock = asyncio.Lock()

async def listen(forms) -> bytes | None:
    target_mac = forms["target"].split("://")[1].replace("-",":")
    raw_bytes = await get_gap_advertisement(target_mac)
    return raw_bytes

async def get_gap_advertisement(target_mac: str) -> bytes | None:
    found_event = asyncio.Event()
    TIME_OUT = 15.0 
    value = None

    def read_once_callback(device: BLEDevice, adv_data: AdvertisementData) -> None:
        nonlocal value 
        
        if device.address.lower() != target_mac.lower():
            return
        if not adv_data.manufacturer_data:
            return
        
        for company_id, raw_bytes in adv_data.manufacturer_data.items():                    
            value = raw_bytes
            break 
                
        found_event.set()
    
    async with scan_lock:
        # Give BlueZ a tiny buffer to finish previous D-Bus teardowns
        await asyncio.sleep(0.5) 
        
        try:
            # The context manager automatically safely handles start() and stop()
            async with BleakScanner(detection_callback=read_once_callback):
                await asyncio.wait_for(found_event.wait(), timeout=TIME_OUT)
        except asyncio.TimeoutError:
            print(f"Timeout: Did not hear from {target_mac} within {TIME_OUT} seconds.")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"Scanner error: {e}")

        return value