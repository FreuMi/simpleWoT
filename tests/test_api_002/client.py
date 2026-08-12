import asyncio
from pathlib import Path

from simplewot import WoT


PLACEHOLDER_DATA = b"action fixture placeholder\n"
EXPECTED_BYTES = bytes.fromhex("a01f")


async def main():
    test_dir = Path(__file__).resolve().parent
    test_file = test_dir / "test_file"
    test_file.write_bytes(PLACEHOLDER_DATA)

    thing = WoT.consume(str(test_dir / "td.json"))

    try:
        await thing.invoke_action("enable")

        disk_data = test_file.read_bytes()
        assert disk_data == EXPECTED_BYTES, f"Expected bytes {EXPECTED_BYTES!r}, got {disk_data!r}"
    finally:
        await thing.cleanup()
        test_file.write_bytes(PLACEHOLDER_DATA)


if __name__ == "__main__":
    asyncio.run(main())
