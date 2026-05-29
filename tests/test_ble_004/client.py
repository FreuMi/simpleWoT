import asyncio

from simplewot.bindings import ble_gatt


FORMS = {
    "target": (
        "gatt://AA-BB-CC-DD-EE-FF/"
        "0000180f-0000-1000-8000-00805f9b34fb/"
        "00002a19-0000-1000-8000-00805f9b34fb"
    )
}


class FakeBleakClient:
    def __init__(self, mac):
        self.mac = mac
        self.is_connected = True
        self.disconnect_called = False

    async def connect(self):
        self.is_connected = True

    async def disconnect(self):
        self.disconnect_called = True
        raise EOFError("dbus connection closed during cleanup")


async def main():
    original_bleak_client = ble_gatt.BleakClient
    ble_gatt.BleakClient = FakeBleakClient

    try:
        client = ble_gatt.AutoDisconnectBleClient(FORMS)
        await client.disconnect()
        assert client.client.disconnect_called is True
    finally:
        ble_gatt.BleakClient = original_bleak_client


if __name__ == "__main__":
    asyncio.run(main())
