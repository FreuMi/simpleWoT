# test_ble_001

Tests BLE GATT target parsing.

It verifies that `ble_gatt.parse_forms_target()` extracts the MAC address, service UUID, and characteristic UUID from a `gatt://` form target, including conversion from dash-separated MAC format to colon-separated format.
