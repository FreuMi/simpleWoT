# test_ble_004

Tests best-effort BLE disconnect cleanup.

It creates an `AutoDisconnectBleClient` with a fake Bleak backend that raises `EOFError` during disconnect. Cleanup should ignore that teardown error instead of failing a successful interaction.
