# test_ble_003

Tests mocked BLE GAP advertisement dispatch.

It replaces `ble_gap.get_gap_advertisement()` with a fake async function and verifies that `ble_gap.listen()` normalizes the MAC address, parses an optional manufacturer ID, and returns advertisement bytes.
