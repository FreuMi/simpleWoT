import asyncio
from bleak import BleakClient

ADDRESS = "A4:C1:38:20:5A:F2"
CHAR_UUID = "ebe0ccc1-7a0a-4b0c-8a1a-6ff2997da3a6"

async def read(mac, service, char) -> bytes:

    raw_bytes = None
    async with BleakClient(mac, services=[service]) as client:
        raw_byte_array = await client.read_gatt_char(char)
        raw_bytes = bytes(raw_byte_array)
    
    return raw_bytes

async def gatt_write(mac: str, service: str, char: str, data: bytes, response: bool = True) -> None:
    async with BleakClient(mac, services=[service]) as client:
        await client.write_gatt_char(char, data, response=response)

async def main():
    value = await read_once_via_notify()
    print(value)

asyncio.run(main())