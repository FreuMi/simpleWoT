import asyncio
import json
import tempfile
from pathlib import Path

from simplewot import Thing
from simplewot.bindings import ble_gatt


GATT_TARGET = (
    "gatt://AA-BB-CC-DD-EE-FF/"
    "0000180f-0000-1000-8000-00805f9b34fb/"
    "00002a19-0000-1000-8000-00805f9b34fb"
)
WRITE_VALUE = "payload"


class FakeBleClient:
    instances = []

    def __init__(self, forms):
        self.forms = forms
        self.calls = []
        self.disconnected = False
        FakeBleClient.instances.append(self)

    async def read(self, forms):
        self.calls.append(("read", forms["methodName"], forms["target"]))
        return b'{"source": "read"}'

    async def read_once_via_notify(self, forms):
        self.calls.append(("notify", forms["methodName"], forms["target"]))
        return b"notified"

    async def write(self, forms, data, response=True):
        self.calls.append(("write", forms["methodName"], data, response, forms["target"]))

    async def disconnect(self):
        self.disconnected = True


def write_runtime_td() -> Path:
    td = {
        "@context": [
            "https://www.w3.org/2022/wot/td/v1.1",
            {"htv": "http://www.w3.org/2011/http#"},
        ],
        "title": "mockBleGattApi",
        "securityDefinitions": {"nosec_sc": {"scheme": "nosec"}},
        "security": ["nosec_sc"],
        "properties": {
            "readConfig": {
                "type": "object",
                "readOnly": True,
                "forms": [
                    {
                        "href": GATT_TARGET,
                        "contentType": "application/json",
                        "htv:methodName": "read",
                    }
                ],
            },
            "notifyConfig": {
                "type": "string",
                "readOnly": True,
                "forms": [
                    {
                        "href": GATT_TARGET,
                        "contentType": "text/plain",
                        "htv:methodName": "notify",
                    }
                ],
            },
            "writeConfig": {
                "type": "string",
                "writeOnly": True,
                "forms": [
                    {
                        "href": GATT_TARGET,
                        "contentType": "text/plain",
                        "htv:methodName": "write",
                    }
                ],
            },
            "writeNoResponseConfig": {
                "type": "string",
                "writeOnly": True,
                "forms": [
                    {
                        "href": GATT_TARGET,
                        "contentType": "text/plain",
                        "htv:methodName": "write-without-response",
                    }
                ],
            },
        },
    }

    temp_file = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    with temp_file:
        json.dump(td, temp_file)

    return Path(temp_file.name)


async def main():
    original_client = ble_gatt.AutoDisconnectBleClient
    ble_gatt.AutoDisconnectBleClient = FakeBleClient
    FakeBleClient.instances.clear()
    runtime_td = write_runtime_td()
    thing = Thing(str(runtime_td))

    try:
        read_data = await thing.read("readConfig")
        assert read_data == {"source": "read"}

        notify_data = await thing.read("notifyConfig")
        assert notify_data == "notified"

        await thing.write("writeConfig", WRITE_VALUE)
        await thing.write("writeNoResponseConfig", WRITE_VALUE)

        assert len(FakeBleClient.instances) == 1
        fake = FakeBleClient.instances[0]
        assert fake.calls == [
            ("read", "read", GATT_TARGET),
            ("notify", "notify", GATT_TARGET),
            ("write", "write", b"payload", True, GATT_TARGET),
            ("write", "write-without-response", b"payload", False, GATT_TARGET),
        ]

        await thing.cleanup()
        assert fake.disconnected is True
    finally:
        ble_gatt.AutoDisconnectBleClient = original_client
        runtime_td.unlink(missing_ok=True)


if __name__ == "__main__":
    asyncio.run(main())
