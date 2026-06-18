import asyncio
import json

from simplewot import WoT


TD = "example_descriptions/ruuviTag.td.json"

async def main():
    thing = WoT.consume(TD)

    try:
        today = await thing.read_property("sensors")
        print(today)
    finally:
        await thing.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
