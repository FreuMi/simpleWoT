# test_ble_002

Tests mocked BLE GATT runtime dispatch.

It replaces `AutoDisconnectBleClient` with a fake client and verifies that `Thing.read()` dispatches to GATT read and notify methods, `Thing.write()` dispatches to write with and without response, and `Thing.cleanup()` disconnects the client.
