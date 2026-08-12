import asyncio
from pathlib import Path

from simplewot import WoT


INITIAL_DATA = "Hello from simpleWoT local file test.\n"
WRITE_DATA = "Updated by simpleWoT local file write test.\n"


async def main():
    test_dir = Path(__file__).resolve().parent
    test_file = test_dir / "test_file"
    test_file.write_text(INITIAL_DATA, encoding="utf-8")

    thing = WoT.consume(str(test_dir / "td.json"))

    try:
        await thing.write_property("writeConfig", WRITE_DATA)

        disk_data = test_file.read_text(encoding="utf-8")
        assert disk_data == WRITE_DATA, f"Expected file data {WRITE_DATA!r}, got {disk_data!r}"

        read_data = await thing.read_property("readConfig")
        assert read_data == WRITE_DATA, f"Expected read data {WRITE_DATA!r}, got {read_data!r}"
    finally:
        await thing.cleanup()
        test_file.write_text(INITIAL_DATA, encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
