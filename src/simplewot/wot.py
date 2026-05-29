from . import spa, td_parser
from rdflib import Literal, URIRef
from .bindings import ble_gap, ble_gatt, http, local_file
from .codecs import binary_codec, json_codec, text_codec

TD = "https://www.w3.org/2019/wot/td#"
HTTP_METHOD_DEFAULTS = {
    "readProperty": "GET",
    "writeProperty": "PUT",
    "invokeAction": "POST",
}


class WoT:
    @staticmethod
    def consume(td_identifier: str):
        return ConsumedThing(td_identifier)


def consume(td_identifier: str):
    return WoT.consume(td_identifier)


class ConsumedThing:
    def __init__(self, td_identifier: str):

        # Parse TD as init
        td_string, self.td_location = td_parser.fetch_td(td_identifier)
        td_graph = td_parser.parse_td(td_string)
        self.td_graph = td_parser.add_td_defaults(td_graph)

        self.client = None
        self._spa_state = {}


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

    def _resolve_relative_target(self, forms: dict) -> dict:
        if forms["target"].startswith("."):
            td_path = "/".join(self.td_location.split("/")[:-1])
            relative_path = forms["target"].removeprefix("./")
            forms["target"] = f"{td_path}/{relative_path}"

        return forms


    async def cleanup(self):
        # Disconnect cleanly form device before shutdown
        if self.client != None:
            await self.client.disconnect()

    
    async def read_property(self, property_name: str):
        await self._ensure_preconditions(property_name, "property", [])
        data = await self._read_interaction(property_name, "property")
        self._record_property_state(property_name, data)
        self._apply_effects(property_name, "property", data)
        return data

    async def write_property(self, property_name: str, value):
        await self._ensure_preconditions(property_name, "property", [])
        await self._write_interaction(property_name, value, "property")
        self._record_property_state(property_name, value)
        self._apply_effects(property_name, "property", value)

    async def invoke_action(self, action_name: str, params=None):
        await self._ensure_preconditions(action_name, "action", [])
        await self._write_interaction(action_name, params, "action")
        self._apply_effects(action_name, "action", self._interaction_value(action_name, "action", params))

    def subscribe_event(self, event_name: str):
        raise NotImplementedError("Event subscription is not implemented yet.")

    async def _ensure_preconditions(self, interaction_name: str, affordance_type: str, stack: list[tuple[str, str]]):
        key = (affordance_type, interaction_name)
        if key in stack:
            raise spa.PlanningError(f"Cyclic SPA precondition dependency for {affordance_type} {interaction_name}")

        affordance = spa.affordance_node(self.td_graph, interaction_name, affordance_type)
        if affordance is None:
            return

        for condition in spa.preconditions(self.td_graph, affordance):
            await self._satisfy_condition(condition, stack + [key])
            if not spa.condition_satisfied(condition, self._spa_state):
                raise spa.PlanningError(f"Could not satisfy SPA precondition for {affordance_type} {interaction_name}")

    async def _satisfy_condition(self, condition: spa.Condition, stack: list[tuple[str, str]]):
        if spa.condition_satisfied(condition, self._spa_state):
            return

        for target in spa.condition_targets(condition):
            if target not in self._spa_state:
                property_name = spa.all_property_targets(self.td_graph).get(target)
                if property_name is not None:
                    await self._ensure_preconditions(property_name, "property", stack)
                    data = await self._read_interaction(property_name, "property")
                    self._record_property_state(property_name, data)
                    self._apply_effects(property_name, "property", data)

        if spa.condition_satisfied(condition, self._spa_state):
            return

        for provider_type, provider_name, effect in spa.all_interaction_effects(self.td_graph):
            if (provider_type, provider_name) in stack:
                continue
            if effect.target not in spa.condition_targets(condition):
                continue

            await self._execute_planned_interaction(provider_name, provider_type, effect, stack)
            if spa.condition_satisfied(condition, self._spa_state):
                return

        raise spa.PlanningError("Could not find interactions to satisfy SPA precondition")

    async def _execute_planned_interaction(
        self,
        interaction_name: str,
        affordance_type: str,
        selected_effect: spa.Effect,
        stack: list[tuple[str, str]],
    ):
        await self._ensure_preconditions(interaction_name, affordance_type, stack)

        if affordance_type == "property":
            value = spa.effect_value(selected_effect, self._spa_state)
            await self._write_interaction(interaction_name, value, affordance_type)
            self._record_property_state(interaction_name, value)
            self._apply_effects(interaction_name, affordance_type, value)
        elif affordance_type == "action":
            value = self._interaction_value(interaction_name, affordance_type, None)
            await self._write_interaction(interaction_name, value, affordance_type)
            self._apply_effects(interaction_name, affordance_type, value)
        else:
            raise spa.PlanningError(f"Unsupported planned interaction type: {affordance_type}")

    def _record_property_state(self, property_name: str, value):
        affordance = spa.affordance_node(self.td_graph, property_name, "property")
        if affordance is not None:
            self._spa_state[str(affordance)] = value

    def _apply_effects(self, interaction_name: str, affordance_type: str, value):
        affordance = spa.affordance_node(self.td_graph, interaction_name, affordance_type)
        if affordance is None:
            return

        inputs = self._interaction_inputs(interaction_name, affordance_type, value)
        for effect in spa.effects(self.td_graph, affordance):
            self._spa_state[effect.target] = spa.effect_value(effect, self._spa_state, inputs)

    def _interaction_value(self, interaction_name: str, affordance_type: str, value):
        if value is not None:
            return value
        if affordance_type == "action":
            return self.get_constant(interaction_name)
        return value

    def _interaction_inputs(self, interaction_name: str, affordance_type: str, value) -> dict[str, object]:
        if value is None:
            return {}

        affordance = spa.affordance_node(self.td_graph, interaction_name, affordance_type)
        if affordance is None:
            return {}

        inputs = {str(affordance): value}
        for input_schema in self.td_graph.objects(affordance, URIRef("https://www.w3.org/2019/wot/td#hasInputSchema")):
            inputs[str(input_schema)] = value

        return inputs

    async def _read_interaction(self, attributeName: str, affordance_type: str):
        ################
        # Extract Forms
        forms = self.get_forms(attributeName, affordance_type, "readProperty")
        forms = self._resolve_relative_target(forms)

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
            raw_bytes = http.request(forms)

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

            
    async def _write_interaction(self, attributeName: str, value, affordance_type: str):
        ################
        # Extract Forms
        operation = "invokeAction" if affordance_type == "action" else "writeProperty"
        forms = self.get_forms(attributeName, affordance_type, operation)
        forms = self._resolve_relative_target(forms)

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
            local_file.write(forms, raw_bytes)
        elif (protocol == "http" or protocol == "https"):
            http.request(forms, raw_bytes)

        return None


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
                return str(raw_value)
            elif schema_type.lower() == "integerschema":
                return int(raw_value)
            elif schema_type.lower() == "numberschema":
                return float(raw_value)
            else:
                raise Exception("cont type currently not supported.")

    def get_forms(self, attributeName: str, affordance_type: str | None = None, operation: str | None = None) -> dict:
        affordance_pattern = "?node td:name ?name ; td:hasForm ?form ."
        if affordance_type == "property":
            affordance_pattern = """
            ?thing td:hasPropertyAffordance ?node .
            ?node td:name ?name ;
                    td:hasForm ?form .
            """
        elif affordance_type == "action":
            affordance_pattern = """
            ?thing td:hasActionAffordance ?node .
            ?node td:name ?name ;
                    td:hasForm ?form .
            """

        operation_filter = ""
        init_bindings = {"name": Literal(attributeName)}
        if operation is not None:
            operation_filter = "FILTER (?operationType = ?requestedOperation)"
            init_bindings["requestedOperation"] = URIRef(TD + operation)

        forms_query = """
            PREFIX td:   <https://www.w3.org/2019/wot/td#>
            PREFIX hctl: <https://www.w3.org/2019/wot/hypermedia#>
            PREFIX htv: <http://www.w3.org/2011/http#>

            SELECT ?contentType ?operationType ?target ?methodName
            WHERE {
            """ + affordance_pattern + """

            OPTIONAL { ?form hctl:forContentType ?contentType . }
            OPTIONAL { ?form hctl:hasOperationType ?operationType . }
            OPTIONAL { ?form hctl:hasTarget ?target . }
            OPTIONAL { ?form htv:methodName ?methodName . }
            """ + operation_filter + """
        }
        """

        rows = self.td_graph.query(forms_query, initBindings=init_bindings)

        if len(rows) > 1:
            raise Exception(f"Found more than 1 form. Currently not supported.")
        
        if len(rows) < 1:
            raise Exception(f"Did not find any forms for affordance '{attributeName}'.")
        row = list(rows)[0]
        forms = {
            "contentType": str(row.contentType) if row.contentType is not None else None,
            "operationType": str(row.operationType) if row.operationType is not None else None,
            "target": str(row.target) if row.target is not None else None,
            "methodName": str(row.methodName) if row.methodName is not None else None,
        }
        self._apply_default_method(forms, operation)

        return forms

    def _apply_default_method(self, forms: dict, operation: str | None):
        if forms["methodName"] is not None:
            return

        protocol = forms["target"].split("://")[0] if forms["target"] else None
        if protocol in {"http", "https"} and operation in HTTP_METHOD_DEFAULTS:
            forms["methodName"] = HTTP_METHOD_DEFAULTS[operation]
