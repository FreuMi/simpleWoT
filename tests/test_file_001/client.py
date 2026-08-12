import asyncio
from pathlib import Path

from simplewot import WoT


EXPECTED_DATA = "Hello from simpleWoT local file test.\n"


async def main():
    test_dir = Path(__file__).resolve().parent
    thing = WoT.consume(str(test_dir / "td.json"))

    try:
        data = await thing.read_property("readConfig")
        assert data == EXPECTED_DATA, f"Expected {EXPECTED_DATA!r}, got {data!r}"
    finally:
        await thing.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
