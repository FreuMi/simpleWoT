# test_ble_002

Tests mocked BLE GATT runtime dispatch.

It replaces `AutoDisconnectBleClient` with a fake client and verifies that `read_property()` dispatches to GATT read and notify methods, `write_property()` dispatches to write with and without response, and `cleanup()` disconnects the client.
