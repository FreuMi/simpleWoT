import asyncio

from simplewot import WoT
from simplewot.bindings import ble_gatt


MEASUREMENT_BYTES = bytes.fromhex("eb0000d20400002d2d0f")
EXPECTED_MEASUREMENTS = {
    "brightness": 1234,
    "conductivity": 3885,
    "moisture": 45,
    "temperature": 23.5,
}


class FakeBleClient:
    instances = []

    def __init__(self, forms):
        self.forms = forms
        self.calls = []
        self.disconnected = False
        FakeBleClient.instances.append(self)

    async def read(self, forms):
        self.calls.append(("read", forms["target"]))
        return MEASUREMENT_BYTES

    async def read_once_via_notify(self, forms):
        raise AssertionError("notify should not be used")

    async def write(self, forms, data, response=True):
        self.calls.append(("write", forms["target"], data, response))

    async def disconnect(self):
        self.disconnected = True


async def main():
    original_client = ble_gatt.AutoDisconnectBleClient
    ble_gatt.AutoDisconnectBleClient = FakeBleClient
    FakeBleClient.instances.clear()

    thing = WoT.consume("example_descriptions/xiaomiFlowerCare.td.json")

    try:
        enable_target = thing.get_forms("enable", "action")["target"]
        measurements_target = thing.get_forms("measurements", "property")["target"]

        measurements = await thing.read_property("measurements")
        assert measurements == EXPECTED_MEASUREMENTS, (
            f"Expected {EXPECTED_MEASUREMENTS!r}, got {measurements!r}"
        )

        assert len(FakeBleClient.instances) == 1
        fake = FakeBleClient.instances[0]
        assert fake.calls == [
            ("write", enable_target, bytes.fromhex("a01f"), True),
            ("read", measurements_target),
        ]

        await thing.cleanup()
        assert fake.disconnected is True
    finally:
        ble_gatt.AutoDisconnectBleClient = original_client


if __name__ == "__main__":
    asyncio.run(main())
