import time
import asyncio
import wot


async def main():
    # Create Thing
    #thing = wot.Thing("./xiaomiThermometer.td.json")
    #value = await thing.read("measurements")

    #thing = wot.Thing("./ruuviAir.td.json")
    #value = await thing.read("sensors")

    thing = wot.Thing("./xiaomiFlowerCare.td.json")

    await thing.write("A1FX")
    value = await thing.read("measurements")

    print(value)

if __name__ == "__main__":
    asyncio.run(main())