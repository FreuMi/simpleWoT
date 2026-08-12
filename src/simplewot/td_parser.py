import json
from importlib import resources
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen
import rdflib
from rdflib import Graph

TD_CONTEXT_URLS = {
    "https://www.w3.org/2022/wot/td/v1.1",
    "http://www.w3.org/2022/wot/td/v1.1",
}


def fetch_td(uri: str) -> str:
    """
    Load a Thing Description from a URL, file URI, or local path.

    Args:
        uri: HTTP(S) URL, file:// URI, or relative/absolute file path.

    Returns:
        The resource content decoded as UTF-8.
    """
    parsed = urlparse(uri)

    # If it already has a scheme like http, https, or file, use it as-is
    if parsed.scheme in {"http", "https", "file"}:
        target = uri
    else:
        # Treat it as a filesystem path (relative or absolute)
        target = Path(uri).expanduser().resolve().as_uri()

    # Load data
    with urlopen(target) as f:
        return f.read().decode("utf-8"), target
    

def _load_local_context() -> dict:
    with resources.files("simplewot").joinpath("context.json").open(encoding="utf-8") as f:
        context_document = json.load(f)

    return context_document["@context"]


def _replace_wot_context_urls(value, local_context: dict):
    if isinstance(value, str):
        if value in TD_CONTEXT_URLS:
            return local_context
        return value

    if isinstance(value, list):
        return [_replace_wot_context_urls(item, local_context) for item in value]

    if isinstance(value, dict):
        return {
            key: _replace_wot_context_urls(item, local_context) if key == "@context" else item
            for key, item in value.items()
        }

    return value


def _parse_json_ld_with_local_context(rdf_data: str) -> Graph:
    td_document = json.loads(rdf_data)
    local_context = _load_local_context()
    offline_document = _replace_wot_context_urls(td_document, local_context)

    rdf_graph = rdflib.Graph()
    rdf_graph.parse(data=json.dumps(offline_document), format="json-ld")

    return rdf_graph


def parse_td(rdf_data: str) -> Graph:
    """
    Parse RDF string into an rdflib Graph.
    Tries several common RDF formats and returns the first successful result.

    Args:
        rdf_data: RDF content as a string.

    Returns:
        A parsed graph with common namespaces bound.
    """
    supported_formats = ["json-ld", "turtle", "xml", "nt", "n3"]
    parsed_successfully = False
    parse_errors = []
    for format in supported_formats:
        try:
            temp_graph = rdflib.Graph()
            temp_graph.parse(data=rdf_data, format=format)

            # If parsing succeeds without an exception
            rdf_graph = temp_graph
            parsed_successfully = True
            #print(f"Successfully parsed input data as {format}.")
            break
        except Exception as e:
            if format == "json-ld":
                try:
                    rdf_graph = _parse_json_ld_with_local_context(rdf_data)
                    parsed_successfully = True
                    break
                except Exception as fallback_error:
                    parse_errors.append(f"Attempt to parse as '{format}' failed: {e}")
                    parse_errors.append(f"Attempt to parse as 'json-ld' with local context failed: {fallback_error}")
            else:
                parse_errors.append(f"Attempt to parse as '{format}' failed: {e}")
            continue

    if not parsed_successfully:
        for error in parse_errors:
            print(error)
        raise TypeError(f"Input data could not be parsed in any supported RDF format: {supported_formats}")
    #print(f"Found {len(rdf_graph)} triples.")

    # Bind namespaces
    TD = rdflib.Namespace("https://www.w3.org/2019/wot/td#")
    rdf_graph.bind("td", TD)

    JS = rdflib.Namespace("https://www.w3.org/2019/wot/json-schema#")
    rdf_graph.bind("json-schema", JS)

    HCTL = rdflib.Namespace("https://www.w3.org/2019/wot/hypermedia#")
    rdf_graph.bind("hctl", HCTL)

    XSD = rdflib.Namespace("http://www.w3.org/2001/XMLSchema#")
    rdf_graph.bind("xsd", XSD)

    return rdf_graph


def add_td_defaults(td_graph: Graph) -> Graph:
    # Adds readOnly=false to every property affordance that does not already define readOnly
    td_graph.update(
            """
            PREFIX td: <https://www.w3.org/2019/wot/td#>
            PREFIX json-schema: <https://www.w3.org/2019/wot/json-schema#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

            INSERT {
                ?aff json-schema:readOnly "false"^^xsd:boolean .
            }
            WHERE {
                ?thing td:hasPropertyAffordance ?aff .
                FILTER NOT EXISTS { ?aff json-schema:readOnly ?any . }
            }
            """
        )
    
    # Adds writeOnly=false to every property affordance that does not already define writeOnly
    td_graph.update(
            """
            PREFIX td: <https://www.w3.org/2019/wot/td#>
            PREFIX json-schema: <https://www.w3.org/2019/wot/json-schema#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

            INSERT {
                ?aff json-schema:writeOnly "false"^^xsd:boolean .
            }
            WHERE {
                ?thing td:hasPropertyAffordance ?aff .
                FILTER NOT EXISTS { ?aff json-schema:writeOnly ?any . }
            }
            """
        )
    
    # Adds observable=false (td:isObservable) to every property affordance that does not already define it.
    td_graph.update(
            """
            PREFIX td: <https://www.w3.org/2019/wot/td#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

            INSERT {
                ?aff td:isObservable "false"^^xsd:boolean .
            }
            WHERE {
                ?thing td:hasPropertyAffordance ?aff .
                FILTER NOT EXISTS { ?aff td:isObservable ?any . }
            }
            """
        )
    
    # Adds safe=false to every action affordance that does not already define it.
    td_graph.update(
            """
            PREFIX td: <https://www.w3.org/2019/wot/td#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

            INSERT {
                ?aff td:isSafe "false"^^xsd:boolean .
            }
            WHERE {
                ?thing td:hasActionAffordance ?aff .
                FILTER NOT EXISTS { ?aff td:isSafe ?any . }
            }
            """
        )
    
    # Adds idempotent=false to every action affordance that does not already define it.
    td_graph.update(
            """
            PREFIX td: <https://www.w3.org/2019/wot/td#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

            INSERT {
                ?aff td:isIdempotent "false"^^xsd:boolean .
            }
            WHERE {
                ?thing td:hasActionAffordance ?aff .
                FILTER NOT EXISTS { ?aff td:isIdempotent ?any . }
            }
            """
        )
    
    # Adds contentType="application/json" to every form that does not already define a content type.
    td_graph.update(
            """
            PREFIX td:  <https://www.w3.org/2019/wot/td#>
            PREFIX hctl:<https://www.w3.org/2019/wot/hypermedia#>

            INSERT {
                ?form hctl:forContentType "application/json" .
            }
            WHERE {
                ?aff td:hasForm ?form .
                FILTER NOT EXISTS { ?form hctl:forContentType ?existing . }
            }
            """
        )
    
    # Adds default operations to forms of property affordances:
    # readOnly=true and writeOnly=false → readProperty
    # readOnly=false and writeOnly=true → writeProperty
    # both false → both readProperty and writeProperty
    td_graph.update(
            """
            PREFIX td:          <https://www.w3.org/2019/wot/td#>
            PREFIX hctl:        <https://www.w3.org/2019/wot/hypermedia#>
            PREFIX json-schema: <https://www.w3.org/2019/wot/json-schema#>

            # readOnly=true, writeOnly=false -> readProperty
            INSERT {
            ?form hctl:hasOperationType td:readProperty .
            }
            WHERE {
            ?thing td:hasPropertyAffordance ?aff .
            ?aff td:hasForm ?form ;
                json-schema:readOnly true ;
                json-schema:writeOnly false .
            FILTER NOT EXISTS { ?form hctl:hasOperationType ?existingOp }
            } ;

            # readOnly=false, writeOnly=true -> writeProperty
            INSERT {
            ?form hctl:hasOperationType td:writeProperty .
            }
            WHERE {
            ?thing td:hasPropertyAffordance ?aff .
            ?aff td:hasForm ?form ;
                json-schema:readOnly false ;
                json-schema:writeOnly true .
            FILTER NOT EXISTS { ?form hctl:hasOperationType ?existingOp }
            } ;

            # readOnly=false, writeOnly=false -> both
            INSERT {
            ?form hctl:hasOperationType ?op .
            }
            WHERE {
            ?thing td:hasPropertyAffordance ?aff .
            ?aff td:hasForm ?form ;
                json-schema:readOnly false ;
                json-schema:writeOnly false .
            VALUES ?op { td:readProperty td:writeProperty }
            FILTER NOT EXISTS { ?form hctl:hasOperationType ?existingOp }
            }
            """
        )
    

    # Adds invokeAction to forms belonging to action affordances, if missing.
    td_graph.update(
            """
            PREFIX td:   <https://www.w3.org/2019/wot/td#>
            PREFIX hctl: <https://www.w3.org/2019/wot/hypermedia#>

            INSERT {
            ?form hctl:hasOperationType td:invokeAction .
            }
            WHERE {
            ?thing td:hasActionAffordance ?aff .
            ?aff td:hasForm ?form .
            FILTER NOT EXISTS { ?form hctl:hasOperationType td:invokeAction }
            }
            """
        )
    
    # Adds both subscribeEvent and unsubscribeEvent to forms belonging to event affordances, if missing.
    td_graph.update(
            """
            PREFIX td:   <https://www.w3.org/2019/wot/td#>
            PREFIX hctl: <https://www.w3.org/2019/wot/hypermedia#>

            INSERT {
            ?form hctl:hasOperationType ?op .
            }
            WHERE {
            ?thing a td:Thing ;
                    td:hasEventAffordance ?aff .
            ?aff   td:hasForm ?form .

            VALUES ?op { td:subscribeEvent td:unsubscribeEvent }

            FILTER NOT EXISTS { ?form hctl:hasOperationType ?op }
            }
            """
        )
    
    #print(f"With defaults: {len(td_graph)} triples.")
    return td_graph
