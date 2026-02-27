import asyncio
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

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
        
        if device.address.lower() == target_mac.lower():
            if adv_data.manufacturer_data:
                for company_id, raw_bytes in adv_data.manufacturer_data.items():                    
                    # Store the hex payload in the outer variable
                    value = raw_bytes
                    break 
                
                found_event.set()
    
    async with BleakScanner(read_once_callback):
        try:
            # Wait for the event to be triggered, but give up after 20 seconds
            await asyncio.wait_for(found_event.wait(), timeout=TIME_OUT)
            
        except asyncio.TimeoutError:
            print(f"\nTimeout: Did not hear from {target_mac} within 20 seconds.")
            
    return value