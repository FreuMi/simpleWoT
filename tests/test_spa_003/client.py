import asyncio
from pathlib import Path

from simplewot import PlanningError, WoT
from simplewot import wot


async def main():
    calls = []

    def fake_write(forms, data):
        calls.append(data)

    original_write = wot.local_file.write
    wot.local_file.write = fake_write

    thing = WoT.consume(str(Path(__file__).resolve().parent / "td.json"))

    try:
        try:
            await thing.invoke_action("target")
        except PlanningError:
            pass
        else:
            raise AssertionError("Expected PlanningError")

        assert calls == [], f"Target action should not execute, got {calls!r}"
    finally:
        await thing.cleanup()
        wot.local_file.write = original_write


if __name__ == "__main__":
    asyncio.run(main())
