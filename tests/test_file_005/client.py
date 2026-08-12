import asyncio
from pathlib import Path

from simplewot import WoT


PLACEHOLDER_DATA = b"binary fixture placeholder\n"
FIXTURE_BYTES = bytes.fromhex("29093708fc")
EXPECTED_DATA = {
    "temperature": 23.45,
    "humidity": 55,
    "voltage": 3300,
}


async def main():
    test_dir = Path(__file__).resolve().parent
    test_file = test_dir / "test_file"
    test_file.write_bytes(FIXTURE_BYTES)

    thing = WoT.consume(str(test_dir / "td.json"))

    try:
        data = await thing.read_property("readConfig")
        assert data == EXPECTED_DATA, f"Expected {EXPECTED_DATA!r}, got {data!r}"
    finally:
        await thing.cleanup()
        test_file.write_bytes(PLACEHOLDER_DATA)


if __name__ == "__main__":
    asyncio.run(main())
