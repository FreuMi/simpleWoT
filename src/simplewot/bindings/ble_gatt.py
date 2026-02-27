import asyncio
from bleak import BleakClient


def parse_forms_target(forms: dict) -> tuple[str, str, str]:
    split_forms = forms["target"].split("/")
    mac = split_forms[2].replace("-", ":")
    service = split_forms[3]
    char = split_forms[4]
    return mac, service, char


class AutoDisconnectBleClient:
    def __init__(self, forms: dict, idle_timeout: float = 2.0):
        mac, service, char = parse_forms_target(forms)
        self.mac = mac
        self.idle_timeout = idle_timeout

        self.client = BleakClient(mac)

        self._idle_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        if not self.client.is_connected:
            await self.client.connect()
        self._reset_idle_timer()

    async def disconnect(self) -> None:
        if self._idle_task is not None:
            self._idle_task.cancel()
            self._idle_task = None

        if self.client.is_connected:
            await self.client.disconnect()

    def _reset_idle_timer(self) -> None:
        if self._idle_task is not None:
            self._idle_task.cancel()

        self._idle_task = asyncio.create_task(self._idle_disconnect())

    async def _idle_disconnect(self) -> None:
        try:
            await asyncio.sleep(self.idle_timeout)
            if self.client.is_connected:
                await self.client.disconnect()
        except asyncio.CancelledError:
            pass

    async def read(self, forms: dict) -> bytes:
        mac, service, char = parse_forms_target(forms)
        async with self._lock:
            await self.connect()
            data = await self.client.read_gatt_char(char)
            self._reset_idle_timer()
            return bytes(data)

    async def read_once_via_notify(self, forms: dict, timeout: float = 15.0) -> bytes:
        mac, service, char = parse_forms_target(forms)
        async with self._lock:
            await self.connect()

            got_value = asyncio.Event()
            raw_bytes: bytes | None = None

            def handler(sender, data: bytearray):
                nonlocal raw_bytes
                raw_bytes = bytes(data)
                got_value.set()
                self._reset_idle_timer()  # notification counts as activity

            await self.client.start_notify(char, handler)
            try:
                if timeout is None:
                    await got_value.wait()
                else:
                    await asyncio.wait_for(got_value.wait(), timeout=timeout)
            finally:
                await self.client.stop_notify(char)
                self._reset_idle_timer()

            if raw_bytes is None:
                raise RuntimeError("No notification received")

            return raw_bytes

    async def write(self, forms: dict, data: bytes, response: bool = True) -> None:
        mac, service, char = parse_forms_target(forms)
        async with self._lock:
            await self.connect()
            await self.client.write_gatt_char(char, data, response=response)
            self._reset_idle_timer()