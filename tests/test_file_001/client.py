import asyncio
from pathlib import Path

from simplewot import Thing


EXPECTED_DATA = "Hello from simpleWoT local file test.\n"


async def main():
    test_dir = Path(__file__).resolve().parent
    thing = Thing(str(test_dir / "td.json"))

    try:
        data = await thing.read("readConfig")
        assert data == EXPECTED_DATA, f"Expected {EXPECTED_DATA!r}, got {data!r}"
    finally:
        await thing.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
