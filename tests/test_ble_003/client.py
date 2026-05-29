import asyncio

from simplewot.bindings import ble_gap


async def main():
    calls = []

    async def fake_get_gap_advertisement(target_mac, manufacturer_id):
        calls.append((target_mac, manufacturer_id))
        return b"advertisement"

    original_get_gap_advertisement = ble_gap.get_gap_advertisement
    ble_gap.get_gap_advertisement = fake_get_gap_advertisement

    try:
        data = await ble_gap.listen({"target": "gap://AA-BB-CC-DD-EE-FF"})
        assert data == b"advertisement"

        data = await ble_gap.listen({"target": "gap://AA-BB-CC-DD-EE-FF/004c"})
        assert data == b"advertisement"

        assert calls == [
            ("AA:BB:CC:DD:EE:FF", None),
            ("AA:BB:CC:DD:EE:FF", 0x004C),
        ]
    finally:
        ble_gap.get_gap_advertisement = original_get_gap_advertisement


if __name__ == "__main__":
    asyncio.run(main())
