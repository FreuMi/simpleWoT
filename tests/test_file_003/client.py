import asyncio

from simplewot import Thing


EXPECTED_DATA = {
    "name": "simpleWoT",
    "enabled": True,
    "count": 3,
}


async def main():
    thing = Thing("tests/test_file_003/td.json")

    try:
        data = await thing.read("readConfig")
        assert data == EXPECTED_DATA, f"Expected {EXPECTED_DATA!r}, got {data!r}"
    finally:
        await thing.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
