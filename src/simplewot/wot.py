from . import td_parser
from rdflib import Literal, URIRef
from .bindings import ble_gap, ble_gatt, http, local_file
from .codecs import binary_codec, json_codec, text_codec


class Thing:
    def __init__(self, td_identifier: str):

        # Parse TD as init
        td_string, self.td_location = td_parser.fetch_td(td_identifier)
        td_graph = td_parser.parse_td(td_string)
        self.td_graph = td_parser.add_td_defaults(td_graph)

        self.client = None


    #####################################################################
    # Graph helper functions
    def get_name(self):
        predicate = URIRef("https://www.w3.org/2019/wot/td#title")

        name = None
        for _, _, o in self.td_graph.triples((None, predicate, None)):
            name = str(o)

        if name == None:
            return "thing1"
        else:
            return name

    def get_ttl_td(self):
        return self.td_graph.serialize()


    async def cleanup(self):
        # Disconnect cleanly form device before shutdown
        if self.client != None:
            await self.client.disconnect()

    
    async def read(self, attributeName: str):
        ################
        # Extract Forms
        forms = self.get_forms(attributeName)

        # Handle relative file path
        if forms["target"].startswith("."):
            # New path = td path + rel. path
            td_path = "/".join(self.td_location.split("/")[:-1])
            relative_path = forms["target"].removeprefix("./")
            absolute_path = f"{td_path}/{relative_path}"

            forms["target"] = absolute_path

        ####### READ DATA #######
        # Check protocol
        protocol = forms["target"].split("://")[0]
        raw_bytes = None
        if (protocol == "gap"):
            raw_bytes = await ble_gap.listen(forms)
        elif (protocol == "gatt"):
            if self.client == None:
                self.client = ble_gatt.AutoDisconnectBleClient(forms)

            # Also notify can be read
            if forms["methodName"].lower() == "notify":
                raw_bytes = await self.client.read_once_via_notify(forms)

            elif forms["methodName"].lower() == "read":
                raw_bytes = await self.client.read(forms)
        
        elif (protocol == "http" or protocol == "https"):
            raw_bytes = http.get(forms)

        elif (protocol == "file"):
            raw_bytes = local_file.read(forms)

        else:
            raise Exception("Protocol1 not supported.")

        # Check if successfull
        if raw_bytes == None:
            raise Exception("No data received.")
        
        ####### DECODE DATA #######
        data = None
        if forms["contentType"] == "application/x.binary-data-stream":
            data = binary_codec.decode(raw_bytes, self.td_graph, attributeName)
        elif forms["contentType"] == "application/json":
            data = json_codec.decode(raw_bytes, self.td_graph, attributeName)
        elif forms["contentType"] == "text/plain" or forms["contentType"] == "text/csv":
            data = text_codec.decode(raw_bytes, self.td_graph, attributeName)
        else:
            print("Content-Type not supported")
            raise Exception()
        
        return data

            
    async def write(self, attributeName: str, value = None):
        ################
        # Extract Forms
        forms = self.get_forms(attributeName)

        # Check if value is provdied, else check for constant
        if value == None:
            value = self.get_constant(attributeName)

        ####### ENCODE DATA #######
        raw_bytes = None
        if forms["contentType"].lower() == "application/x.binary-data-stream":
            raw_bytes = binary_codec.encode(value, self.td_graph, attributeName)
        elif forms["contentType"].lower() == "application/json":
            raw_bytes = json_codec.encode(value, self.td_graph, attributeName)
        elif forms["contentType"] == "text/plain" or forms["contentType"] == "text/csv":
            raw_bytes = text_codec.encode(value, self.td_graph, attributeName)
        else:
            raise Exception("Content-Type not supported")
        
        if raw_bytes == None:
            raise Exception("Data could not be encoded.")
        
        ####### WRITE DATA #######
        # Check protocol
        protocol = forms["target"].split("://")[0]

        if (protocol == "gatt"):
            if self.client == None:
                self.client = ble_gatt.AutoDisconnectBleClient(forms)

            # Write data separate if response is needed
            if forms["methodName"].lower() == "write-without-response":
                raw_bytes = await self.client.write(forms, raw_bytes, False)
            elif forms["methodName"].lower() == "write":
                raw_bytes = await self.client.write(forms, raw_bytes, True)
            else:
                raise Exception("Operation not supported.")
        elif (protocol == "file"):
            raw_bytes = local_file.write(forms, raw_bytes)
        elif (protocol == "http" or protocol == "https"):
            if forms["methodName"].lower() == "put":
                raw_bytes = http.put(forms, raw_bytes)
            else:
                raise Exception("Operation not supported.")

        return raw_bytes

    def subscribe(self, attributeName: str):
        pass


    def get_constant(self, attributeName):
        ## Query action
        query = """
            PREFIX td:          <https://www.w3.org/2019/wot/td#>
            PREFIX json-schema: <https://www.w3.org/2019/wot/json-schema#>
            PREFIX bdo:         <https://paul.ti.rw.fau.de/~jo00defe/ble/bdo#>

            SELECT ?const ?schemaType
            WHERE {
            ?thing td:hasActionAffordance ?action .
            ?action td:name ?name ;
                    td:hasInputSchema ?schema .
                    ?schema a ?schemaType .

            OPTIONAL { ?schema json-schema:const ?const . }
            }
            """
        
        rows = list(self.td_graph.query(query, initBindings={"name": Literal(attributeName)}))
        if len(rows) == 1:
            schema_type = rows[0]["schemaType"].split("#")[-1]
            raw_value = rows[0]["const"]
            if schema_type.lower() == "stringschema":
                value = str(raw_value)
                return value
            else:
                raise Exception("cont type currently not supported.")

    def get_forms(self, attributeName: str) -> dict:
        forms_query = """
            PREFIX td:   <https://www.w3.org/2019/wot/td#>
            PREFIX hctl: <https://www.w3.org/2019/wot/hypermedia#>
            PREFIX htv: <http://www.w3.org/2011/http#>

            SELECT ?contentType ?operationType ?target ?methodName
            WHERE {
            ?node td:name ?name ;
                    td:hasForm ?form .

            OPTIONAL { ?form hctl:forContentType ?contentType . }
            OPTIONAL { ?form hctl:hasOperationType ?operationType . }
            OPTIONAL { ?form hctl:hasTarget ?target . }
            OPTIONAL { ?form htv:methodName ?methodName . }
        }
        """

        rows = self.td_graph.query(forms_query, initBindings={"name": Literal(attributeName)})

        if len(rows) > 1:
            raise Exception(f"Found more than 1 form. Currently not supported.")
        
        if len(rows) < 1:
            raise Exception(f"Did not find any forms for affordance '{attributeName}'.")
        row = list(rows)[0]
        forms = {"contentType": str(row.contentType), "operationType": str(row.operationType), "target": str(row.target), "methodName": str(row.methodName)}

        return forms
