import asyncio
from pathlib import Path

from simplewot import Thing


PLACEHOLDER_DATA = b"binary fixture placeholder\n"
INITIAL_BYTES = bytes.fromhex("29093708fc")
WRITE_DATA = {
    "temperature": -4.5,
    "humidity": 80,
    "voltage": 4200,
}
EXPECTED_BYTES = bytes.fromhex("3efe500c80")


async def main():
    test_dir = Path(__file__).resolve().parent
    test_file = test_dir / "test_file"
    test_file.write_bytes(INITIAL_BYTES)

    thing = Thing(str(test_dir / "td.json"))

    try:
        await thing.write("writeConfig", WRITE_DATA)

        disk_data = test_file.read_bytes()
        assert disk_data == EXPECTED_BYTES, f"Expected bytes {EXPECTED_BYTES!r}, got {disk_data!r}"

        read_data = await thing.read("readConfig")
        assert read_data == WRITE_DATA, f"Expected read data {WRITE_DATA!r}, got {read_data!r}"
    finally:
        await thing.cleanup()
        test_file.write_bytes(PLACEHOLDER_DATA)


if __name__ == "__main__":
    asyncio.run(main())
