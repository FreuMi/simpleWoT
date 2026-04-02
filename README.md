# simpleWoT

**simpleWoT** is a lightweight Python implementation of the **Web of Things Scripting API**. It provides a convenient way to interact with WoT Thing Descriptions (TDs) and perform read/write operations on properties and actions using various protocols (HTTP, BLE GATT, BLE GAP, local files).

---

## Installation

```bash
pip install simpleWoT
```

---

## Quick Start

```python
import asyncio
from simplewot import Thing

async def main():
    # Initialise a Thing using a Thing Description (TD) URL or local file path
    td_path = "example_descriptions/xiaomiThermometer.td.json"
    thing = Thing(td_path)

    # Read a property (e.g., temperature)
    temperature = await thing.read("temperature")
    print("Temperature:", temperature)

    # Write to a writable property (if supported)
    # await thing.write("ledState", True)

# Run the async main function
asyncio.run(main())
```

The `Thing` class automatically parses the TD, resolves defaults, and selects the appropriate protocol based on the forms defined in the description.

---

## API Overview

- **`Thing(td_identifier: str)`** – Construct a Thing from a TD identifier (URL, `file://` URI, or filesystem path).
- **`await thing.read(attribute_name: str)`** – Read the value of a property or the result of an action.
- **`await thing.write(attribute_name: str, value)`** – Write a value to a writable property.
- **`await thing.cleanup()`** – Cleanly disconnect any underlying BLE connections.
- **`thing.get_name()`** – Retrieve the human‑readable name of the Thing.
- **`thing.get_ttl_td()`** – Get the serialized TD in Turtle format.

For detailed behaviour, see the source files in `src/simplewot/`.

---

## License

This project is licensed under the **GNU Affero General Public License v3.0**. See the `LICENSE` file for the full terms.
