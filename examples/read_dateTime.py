import asyncio
import json

from simplewot import WoT


TD = "example_descriptions/dateTimeService.td.json"

async def main():
    thing = WoT.consume(TD)

    try:
        today = await thing.read_property("today")
        print(today)
    finally:
        await thing.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
