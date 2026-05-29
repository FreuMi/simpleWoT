# simpleWoT

`simpleWoT` is a small Python library for consuming W3C Web of Things Thing Descriptions and interacting with Things through a minimal async API.

It is built for practical WoT integrations rather than full framework complexity: load a TD, resolve its forms, fetch bytes through the matching binding, and decode them into Python values.

The current implementation includes built-in bindings for:

- BLE GATT
- BLE GAP advertisements
- HTTP `GET`
- local files

It is especially geared toward BLE sensor integrations such as the bundled examples in [`example_descriptions/`](/home/freumi/Desktop/simpleWoT/example_descriptions).

## Why This Project

`simpleWoT` is useful when you want:

- a lightweight WoT client in Python
- to work directly from a Thing Description instead of writing device-specific parsing code
- to decode BLE advertisement or GATT payloads described with `bdo:*` metadata
- a small codebase that is easy to inspect and extend

If you need broad WoT platform coverage, advanced protocol support, or the full WoT Scripting API, this repository is intentionally narrower than that.

## Highlights

- Minimal async API centered on `WoT.consume()` and `ConsumedThing`
- Supports TD sources from URLs, `file://` URIs, and local paths
- Parses RDF-based TDs including JSON-LD and Turtle
- Includes binary, JSON, and plain-text payload decoding
- Can execute same-Thing SPA preconditions automatically before requested interactions
- Ships with working BLE-oriented example TDs

## Status

This project is an early, minimal implementation. It already works for a useful subset of WoT use cases, but it does not aim to cover the full WoT Scripting API yet.

Current notable limitations:

- `ConsumedThing.read_property()` supports a single form per affordance.
- `ConsumedThing.write_property()` currently supports `gatt://`, `http://`, `https://`, and `file://` targets.
- HTTP support is read-only and only issues simple `GET` requests.
- Event subscription is not implemented yet (`ConsumedThing.subscribe_event()` raises `NotImplementedError`).
- Binary decoding is focused on object schemas with integer/number fields described via `bdo:*` metadata.
- Binary encoding is limited compared to decoding and mainly supports integer values and hex-formatted strings.
- SPA planning is currently single-Thing and supports a practical subset of conditions and effects.

## Requirements

- Python `>=3.12`
- Linux BLE stack support for BLE features (`bleak` / `dbus-fast`, typically BlueZ)

Project dependencies are declared in [`pyproject.toml`](/home/freumi/Desktop/simpleWoT/pyproject.toml).

## Installation

From the repository root:

```bash
pip install .
```

For editable local development:

```bash
pip install -e .
```

## Supported TD Inputs

You can consume a TD from:

- an `http://` or `https://` URL
- a `file://` URI
- a relative or absolute local path

TD content is parsed as RDF. The parser tries these formats in order:

- JSON-LD
- Turtle
- RDF/XML
- N-Triples
- N3

## Quick Start

Read measurements from the bundled Xiaomi thermometer TD:

```python
import asyncio
from simplewot import WoT

async def main():
    thing = WoT.consume("example_descriptions/xiaomiThermometer.td.json")
    measurements = await thing.read_property("measurements")
    print(measurements)
    await thing.cleanup()

asyncio.run(main())
```

For the Xiaomi thermometer example, `measurements` resolves to a Python `dict` containing decoded values such as temperature and humidity.

## Examples

### Read BLE advertisement data

```python
import asyncio
from simplewot import WoT

async def main():
    thing = WoT.consume("example_descriptions/ruuviAir.td.json")
    sensors = await thing.read_property("sensors")
    print("Temperature:", sensors["temperature"])
    print("Humidity:", sensors["humidity"])
    await thing.cleanup()

asyncio.run(main())
```

### Invoke an action using a TD constant

If a TD action input defines a `const`, `invoke_action()` can use it automatically when you omit the value:

```python
import asyncio
from simplewot import WoT

async def main():
    thing = WoT.consume("example_descriptions/xiaomiFlowerCare.td.json")
    await thing.invoke_action("enable")
    measurements = await thing.read_property("measurements")
    print(measurements)
    await thing.cleanup()

asyncio.run(main())
```

### Provide an explicit property write value

```python
await thing.write_property("someProperty", value)
```

## API Overview

### `WoT.consume(td_identifier: str)`

Loads the TD, parses it into an RDF graph, and applies a few WoT default values such as missing content types and default operation types.

Returns a `ConsumedThing`.

### `await thing.read_property(property_name: str)`

Finds the affordance form, fetches raw bytes through the matching binding, and decodes the payload based on the declared content type.

Supported content types:

- `application/x.binary-data-stream`
- `application/json`
- `text/plain`

### `await thing.write_property(property_name: str, value)`

Encodes a value using the affordance schema and writes it through the selected binding.

### `await thing.invoke_action(action_name: str, params=None)`

Invokes an action affordance. If `params` is omitted, the implementation tries to read a constant input value from the TD action schema.

If the requested interaction has SPA preconditions, `simpleWoT` tries to satisfy them first by reading properties or executing same-Thing interactions whose effects establish the required state. If no safe plan can be found, a `PlanningError` is raised.

### `await thing.cleanup()`

Disconnects an active BLE GATT client if one was opened.

### `thing.get_name()`

Returns the TD title, or `"thing1"` if none is present.

### `thing.get_ttl_td()`

Serializes the parsed TD graph.

## License

Licensed under the GNU Affero General Public License v3.0. See [`LICENSE`](/home/freumi/Desktop/simpleWoT/LICENSE).
