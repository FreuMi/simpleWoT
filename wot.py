import td_parser
from rdflib import Literal
import ble_gap
import ble_gatt
import binary_codec

class Thing:
    def __init__(self, td_identifier: str):

        # Parse TD as init
        td_string = td_parser.fetch_td(td_identifier)
        td_graph = td_parser.parse_td(td_string)
        self.td_graph = td_parser.add_td_defaults(td_graph)

        self.client = None

        
    async def read(self, attributeName: str):
        ################
        # Extract Forms
        forms = self.get_forms(attributeName)

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
                raw_bytes = await ble_gatt.read_once_via_notify(forms)

            elif forms["methodName"].lower() == "read":
                raw_bytes = await self.client.read(forms)

        else:
            print("Protocol not supported.")

        # Check if successfull
        if raw_bytes == None:
            raise Exception("No data received.")
        
        print(raw_bytes)

        ####### DECODE DATA #######
        data = None
        if forms["contentType"] == "application/x.binary-data-stream":
            data = binary_codec.decode(raw_bytes, self.td_graph, attributeName)
        else:
            print("Content-Type not supported")
            raise Exception()
        
        return data

            
    def write(self, attributeName: str, value):
        pass

    def subscribe(self, attributeName: str):
        pass


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
            print(f"Found more than 1 form. Currently not supported.")
            raise Exception()

        row = list(rows)[0]
        forms = {"contentType": str(row.contentType), "operationType": str(row.operationType), "target": str(row.target), "methodName": str(row.methodName)}

        return forms
