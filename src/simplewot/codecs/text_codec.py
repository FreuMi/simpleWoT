from rdflib import Graph

def decode(raw_bytes: bytes, td_graph: Graph, attributeName: str) -> str:
    data_string = raw_bytes.decode("utf-8")

    return data_string

def encode(data: str, td_graph: Graph, attributeName: str) -> bytes:
    raw_bytes = data.encode("utf-8")
    
    return raw_bytes