# test_spa_005

Tests the Xiaomi Flower Care enable-before-read behavior.

It consumes the real Flower Care example TD with mocked GATT, calls `read_property("measurements")`, and verifies that the SPA precondition invokes `enable` before the measurement read while reusing one GATT client instance.
