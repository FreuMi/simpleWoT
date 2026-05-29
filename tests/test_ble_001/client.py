from simplewot.bindings import ble_gatt


def main():
    forms = {
        "target": "gatt://AA-BB-CC-DD-EE-FF/0000180f-0000-1000-8000-00805f9b34fb/00002a19-0000-1000-8000-00805f9b34fb"
    }

    mac, service, char = ble_gatt.parse_forms_target(forms)

    assert mac == "AA:BB:CC:DD:EE:FF"
    assert service == "0000180f-0000-1000-8000-00805f9b34fb"
    assert char == "00002a19-0000-1000-8000-00805f9b34fb"


if __name__ == "__main__":
    main()
