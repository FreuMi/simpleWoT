import asyncio
import json
from pathlib import Path

from simplewot import Thing


INITIAL_DATA = {
    "name": "simpleWoT",
    "enabled": True,
    "count": 3,
}
WRITE_DATA = {
    "name": "simpleWoT",
    "enabled": False,
    "count": 4,
    "tags": ["json", "write"],
}


def write_json(path: Path, data: dict):
    path.write_text(json.dumps(data), encoding="utf-8")


async def main():
    test_dir = Path(__file__).resolve().parent
    test_file = test_dir / "test_file"
    write_json(test_file, INITIAL_DATA)

    thing = Thing(str(test_dir / "td.json"))

    try:
        await thing.write("writeConfig", WRITE_DATA)

        disk_data = json.loads(test_file.read_text(encoding="utf-8"))
        assert disk_data == WRITE_DATA, f"Expected file data {WRITE_DATA!r}, got {disk_data!r}"

        read_data = await thing.read("readConfig")
        assert read_data == WRITE_DATA, f"Expected read data {WRITE_DATA!r}, got {read_data!r}"
    finally:
        await thing.cleanup()
        write_json(test_file, INITIAL_DATA)


if __name__ == "__main__":
    asyncio.run(main())
