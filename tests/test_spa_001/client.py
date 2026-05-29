import asyncio
from pathlib import Path

from simplewot import WoT
from simplewot import wot


async def main():
    calls = []

    def fake_write(forms, data):
        calls.append(data.decode("utf-8"))

    original_write = wot.local_file.write
    wot.local_file.write = fake_write

    thing = WoT.consume(str(Path(__file__).resolve().parent / "td.json"))

    try:
        await thing.invoke_action("target")
        assert calls == ["prepare", "target"], f"Expected prerequisite order, got {calls!r}"
    finally:
        await thing.cleanup()
        wot.local_file.write = original_write


if __name__ == "__main__":
    asyncio.run(main())
