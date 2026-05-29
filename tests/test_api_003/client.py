import asyncio
from pathlib import Path

from simplewot import WoT


WRITE_DATA = "updated-write-target\n"


async def main():
    test_dir = Path(__file__).resolve().parent
    write_file = test_dir / "write_file"
    original_write_data = write_file.read_text(encoding="utf-8")

    thing = WoT.consume(str(test_dir / "td.json"))

    try:
        read_data = await thing.read_property("config")
        assert read_data == "read-target\n", f"Expected read form data, got {read_data!r}"

        await thing.write_property("config", WRITE_DATA)
        assert write_file.read_text(encoding="utf-8") == WRITE_DATA
        assert (test_dir / "read_file").read_text(encoding="utf-8") == "read-target\n"
    finally:
        await thing.cleanup()
        write_file.write_text(original_write_data, encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
