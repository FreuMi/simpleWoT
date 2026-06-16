import asyncio
import json

from simplewot import WoT


TD = "example_descriptions/ruuviAir.td.json"


async def main():
    thing = WoT.consume(TD)

    try:
        measurements = await thing.read_property("sensors")
        print(json.dumps(measurements, indent=2))
    finally:
        await thing.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
