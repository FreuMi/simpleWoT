from rdflib import Graph, Literal

def decode(raw_bytes: bytes, td_graph: Graph, attributeName: str):
    schema = get_schema_properties(td_graph, attributeName)

    if schema["type"].lower() == "objectschema":
        result_object = {}

        properties = schema["properties"]

        for property_name, prop in properties.items():
            prop_type = prop["type"].lower()

            if prop_type in {"integerschema", "numberschema"}:
                result_object[property_name] = decode_number_or_int(raw_bytes, prop)
            else:
                raise ValueError(f"Unsupported property type: {prop['type']}")

        return result_object

    raise ValueError(f"Unsupported schema type: {schema['type']}")


def decode_number_or_int(raw_bytes: bytes, field: dict) -> int | float:
    # New format: ordered fragments
    if "fragments" in field:
        fragments = sorted(field["fragments"], key=lambda f: f["index"])
        value = 0
        total_len = 0

        for fragment in fragments:
            part = extract_bits(
                raw_bytes,
                fragment["bitOffset"],
                fragment["bitLength"],
            )
            value = (value << fragment["bitLength"]) | part
            total_len += fragment["bitLength"]

    else:
        bit_offset = field["bitOffset"]
        bit_length = field["bitLength"]

        if isinstance(bit_offset, list):
            if not isinstance(bit_length, list) or len(bit_offset) != len(bit_length):
                raise ValueError("bitOffset and bitLength must both be lists of equal length")

            value = 0
            total_len = 0
            for off, length in zip(bit_offset, bit_length, strict=True):
                part = extract_bits(raw_bytes, off, length)
                value = (value << length) | part
                total_len += length

        else:
            total_len = bit_length

            # Prefer byte-wise decoding when aligned
            if bit_offset % 8 == 0 and bit_length % 8 == 0:
                byte_offset = bit_offset // 8
                byte_length = bit_length // 8
                chunk = raw_bytes[byte_offset:byte_offset + byte_length]

                byte_order = field.get("byteOrder", "little").lower()
                if byte_order in {"little", "littleendian"}:
                    order = "little"
                elif byte_order in {"big", "bigendian"}:
                    order = "big"
                else:
                    raise ValueError(f"Unsupported byteOrder: {byte_order}")

                value = int.from_bytes(chunk, byteorder=order, signed=False)
            else:
                value = extract_bits(raw_bytes, bit_offset, bit_length)

    if field.get("signed", False):
        value = to_signed(value, total_len)

    if "scale" in field:
        value *= field["scale"]
    if "valueAdd" in field:
        value += field["valueAdd"]

    schema_type = field.get("type")
    if schema_type == "IntegerSchema":
        return int(value)
    if schema_type == "NumberSchema":
        return round(float(value), 2)

    return value

def extract_bits(raw_bytes: bytes, bit_offset: int, bit_length: int) -> int:
    """
    Extract bit_length bits starting at bit_offset from raw_bytes.

    Bit 0 is the most significant bit of raw_bytes[0].
    """
    total_bits = len(raw_bytes) * 8

    if bit_offset < 0 or bit_length <= 0:
        raise ValueError("bit_offset must be >= 0 and bit_length must be > 0")
    if bit_offset + bit_length > total_bits:
        raise ValueError("Requested bits exceed raw_bytes length")

    value = int.from_bytes(raw_bytes, byteorder="big", signed=False)
    shift = total_bits - bit_offset - bit_length
    mask = (1 << bit_length) - 1

    return (value >> shift) & mask

##########################################################################################

def encode(value, td_graph: Graph, attributeName: str):

    schema = get_schema_properties(td_graph, attributeName)
    if schema["type"] == None:
        schema = get_action_schema(td_graph, attributeName)

    # Add defaults
    if schema["byteOrder"] == None:
        schema["byteOrder"] = "little"

    if schema["signed"] == None:
        schema["signed"] = True

    if schema["bitLength"] == None:
        schema["bitLength"] = 8

    # Calculate byte length
    byteLength = int(schema["bitLength"]/8)

    if schema["type"].lower() == "integerschema":
        raw_bytes = int(value).to_bytes(byteLength, byteorder= schema["byteOrder"], signed=schema["signed"])
        return raw_bytes
    
    elif schema["type"].lower() == "numberschema":
        pass

##########################################################################################
def to_bool(value: str) -> bool:
        return value.strip().lower() == "true"

def to_signed(value: int, bit_length: int) -> int:
    sign_bit = 1 << (bit_length - 1)
    if value & sign_bit:
        return value - (1 << bit_length)
    return value


# Function to extract schema
def get_schema_properties(g: Graph, attributeName: str):
    query = """
    PREFIX td:          <https://www.w3.org/2019/wot/td#>
    PREFIX json-schema: <https://www.w3.org/2019/wot/json-schema#>
    PREFIX bdo:         <https://paul.ti.rw.fau.de/~jo00defe/ble/bdo#>

    SELECT ?schemaType
        ?propName ?propType
        ?bitOffset ?bitLength ?byteOrder ?signed ?scale ?valueAdd
        ?fragment ?fragmentIndex ?fragmentBitOffset ?fragmentBitLength
    WHERE {
    ?schema td:name ?name ;
            a ?schemaType .

    OPTIONAL {
        ?schema json-schema:properties ?prop .
        ?prop td:name ?propName ;
            a ?propType .

        OPTIONAL { ?prop bdo:bitOffset ?bitOffset . }
        OPTIONAL { ?prop bdo:bitLength ?bitLength . }
        OPTIONAL { ?prop bdo:byteOrder ?byteOrder . }
        OPTIONAL { ?prop bdo:signed ?signed . }
        OPTIONAL { ?prop bdo:scale ?scale . }
        OPTIONAL { ?prop bdo:valueAdd ?valueAdd . }

        OPTIONAL {
        ?prop bdo:fragments ?fragment .
        ?fragment bdo:index ?fragmentIndex ;
                    bdo:bitOffset ?fragmentBitOffset ;
                    bdo:bitLength ?fragmentBitLength .
        }
    }
    }
    ORDER BY ?propName ?fragmentIndex ?bitOffset ?bitLength
    """

    rows = g.query(query, initBindings={"name": Literal(attributeName)})

    result = {
        "type": None,
        "properties": {}
    }

    def local_name(term) -> str | None:
        if term is None:
            return None
        text = str(term)
        if "#" in text:
            return text.rsplit("#", 1)[-1]
        return text.rsplit("/", 1)[-1]

    def to_py(value):
        if value is None:
            return None
        return value.toPython() if hasattr(value, "toPython") else value

    def add_value(prop_dict: dict, key: str, value):
        if value is None:
            return

        py_value = to_py(value)

        if key not in prop_dict:
            prop_dict[key] = py_value
            return

        existing = prop_dict[key]
        if isinstance(existing, list):
            if py_value not in existing:
                existing.append(py_value)
        else:
            if py_value != existing:
                prop_dict[key] = [existing, py_value]

    for row in rows:
        if result["type"] is None and row.schemaType:
            result["type"] = local_name(row.schemaType)

        if not row.propName:
            continue

        prop_name = str(row.propName)

        if prop_name not in result["properties"]:
            result["properties"][prop_name] = {}

        prop = result["properties"][prop_name]

        if row.propType and "type" not in prop:
            prop["type"] = local_name(row.propType)

        # Simple (non-fragmented) fields
        add_value(prop, "bitOffset", row.bitOffset)
        add_value(prop, "bitLength", row.bitLength)
        add_value(prop, "byteOrder", row.byteOrder)
        add_value(prop, "signed", row.signed)
        add_value(prop, "scale", row.scale)
        add_value(prop, "valueAdd", row.valueAdd)

        # Fragmented fields
        if row.fragment is not None:
            if "fragments" not in prop:
                prop["fragments"] = []

            fragment_info = {
                "index": to_py(row.fragmentIndex),
                "bitOffset": to_py(row.fragmentBitOffset),
                "bitLength": to_py(row.fragmentBitLength),
            }

            if fragment_info not in prop["fragments"]:
                prop["fragments"].append(fragment_info)

    # Keep fragments ordered
    for prop in result["properties"].values():
        if "fragments" in prop:
            prop["fragments"].sort(key=lambda f: f["index"])

            # Optional: remove old direct bit fields if fragments are present
            prop.pop("bitOffset", None)
            prop.pop("bitLength", None)

    return result


def get_action_schema(g: Graph, action_name: str):
    query = """
    PREFIX td:          <https://www.w3.org/2019/wot/td#>
    PREFIX json-schema: <https://www.w3.org/2019/wot/json-schema#>
    PREFIX bdo:         <https://paul.ti.rw.fau.de/~jo00defe/ble/bdo#>

    SELECT ?schemaType ?const ?format ?description
           ?byteLength ?bitLength ?bitOffset ?byteOrder ?signed ?scale ?valueAdd
    WHERE {
      ?thing td:hasActionAffordance ?action .
      ?action td:name ?name ;
              td:hasInputSchema ?schema .

      ?schema a ?schemaType .

      OPTIONAL { ?schema json-schema:const ?const . }
      OPTIONAL { ?schema json-schema:format ?format . }
      OPTIONAL { ?schema td:description ?description . }

      OPTIONAL { ?schema bdo:bytelength ?byteLength . }
      OPTIONAL { ?schema bdo:bitLength ?bitLength . }
      OPTIONAL { ?schema bdo:bitOffset ?bitOffset . }
      OPTIONAL { ?schema bdo:byteOrder ?byteOrder . }
      OPTIONAL { ?schema bdo:signed ?signed . }
      OPTIONAL { ?schema bdo:scale ?scale . }
      OPTIONAL { ?schema bdo:valueAdd ?valueAdd . }
    }
    """

    rows = list(g.query(query, initBindings={"name": Literal(action_name)}))
    if not rows:
        return None

    row = rows[0]

    def local_name(term):
        if term is None:
            return None
        text = str(term)
        if "#" in text:
            return text.rsplit("#", 1)[-1]
        return text.rsplit("/", 1)[-1]

    def to_py(value):
        if value is None:
            return None
        return value.toPython() if hasattr(value, "toPython") else value

    return {
        "type": local_name(row.schemaType),
        "const": to_py(row.const),
        "format": to_py(row.format),
        "description": to_py(row.description),
        "byteLength": to_py(row.byteLength),
        "bitLength": to_py(row.bitLength),
        "bitOffset": to_py(row.bitOffset),
        "byteOrder": to_py(row.byteOrder),
        "signed": to_py(row.signed),
        "scale": to_py(row.scale),
        "valueAdd": to_py(row.valueAdd),
    }