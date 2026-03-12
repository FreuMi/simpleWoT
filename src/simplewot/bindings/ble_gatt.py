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
        self._shutting_down = False

        self.client = BleakClient(mac)

        self._idle_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        if not self.client.is_connected:
            await self.client.connect()
        # We REMOVED the timer reset from here, as the caller handles it now.

    async def disconnect(self) -> None:
        self._shutting_down = True
        self._cancel_idle_timer()

        if self.client.is_connected:
            await self.client.disconnect()

    def _cancel_idle_timer(self) -> None:
        """Stops the disconnect countdown during active work."""
        if self._idle_task is not None:
            self._idle_task.cancel()
            self._idle_task = None

    def _reset_idle_timer(self) -> None:
        """Starts the disconnect countdown when idle."""
        if self._shutting_down:
            return
        
        self._cancel_idle_timer()
        self._idle_task = asyncio.create_task(self._idle_disconnect())

    async def _idle_disconnect(self) -> None:
        try:
            await asyncio.sleep(self.idle_timeout)
            if self._shutting_down:
                return
            if self.client.is_connected:
                print(f"Idle timeout reached. Disconnecting from {self.mac}")
                await self.client.disconnect()
        except asyncio.CancelledError:
            pass

    async def read(self, forms: dict) -> bytes:
        mac, service, char = parse_forms_target(forms)
        async with self._lock:
            self._cancel_idle_timer()  # Pause timer while working
            try:
                await self.connect()
                data = await self.client.read_gatt_char(char)
                return bytes(data)
            finally:
                self._reset_idle_timer()  # Resume timer when done

    async def read_once_via_notify(self, forms: dict, timeout: float = 15.0) -> bytes:
        mac, service, char = parse_forms_target(forms)
        async with self._lock:
            self._cancel_idle_timer() # Pause timer while working
            try:
                await self.connect()

                got_value = asyncio.Event()
                raw_bytes: bytes | None = None

                def handler(sender, data: bytearray):
                    nonlocal raw_bytes
                    raw_bytes = bytes(data)
                    got_value.set()

                await self.client.start_notify(char, handler)
                try:
                    if timeout is None:
                        await got_value.wait()
                    else:
                        await asyncio.wait_for(got_value.wait(), timeout=timeout)
                finally:
                    await self.client.stop_notify(char)

                if raw_bytes is None:
                    raise RuntimeError("No notification received")

                return raw_bytes
            finally:
                self._reset_idle_timer() # Resume timer when done

    async def write(self, forms: dict, data: bytes, response: bool = True) -> None:
        mac, service, char = parse_forms_target(forms)
        async with self._lock:
            self._cancel_idle_timer() # Pause timer while working
            try:
                await self.connect()
                await self.client.write_gatt_char(char, data, response=response)
            finally:
                self._reset_idle_timer() # Resume timer when done