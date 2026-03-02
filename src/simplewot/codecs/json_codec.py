from rdflib import Graph
import json

def decode(raw_bytes: bytes, td_graph: Graph, attributeName: str):
    data_string = raw_bytes.decode("utf-8")
    data = json.loads(data_string)

    return data