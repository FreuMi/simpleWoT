from dataclasses import dataclass

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.namespace import RDF


SPA = Namespace("https://paul.ti.rw.fau.de/~jo00defe/voc/spa#")
TD = Namespace("https://www.w3.org/2019/wot/td#")

PRECONDITION_PREDICATES = (SPA.precondition, TD.precondition)
EFFECT_PREDICATES = (SPA.effect, TD.effect)


class PlanningError(Exception):
    pass


@dataclass
class Condition:
    kind: str
    args: list


@dataclass
class Effect:
    target: str
    value: object


@dataclass
class ValueRef:
    target: str


@dataclass
class NumericAdd:
    left: object
    right: object


def affordance_node(graph: Graph, name: str, affordance_type: str):
    predicate = TD.hasPropertyAffordance if affordance_type == "property" else TD.hasActionAffordance
    rows = list(
        graph.query(
            """
            PREFIX td: <https://www.w3.org/2019/wot/td#>

            SELECT ?affordance
            WHERE {
                ?thing ?predicate ?affordance .
                ?affordance td:name ?name .
            }
            """,
            initBindings={"predicate": predicate, "name": Literal(name)},
        )
    )

    if len(rows) != 1:
        return None

    return rows[0]["affordance"]


def all_property_targets(graph: Graph) -> dict[str, str]:
    rows = list(
        graph.query(
            """
            PREFIX td: <https://www.w3.org/2019/wot/td#>

            SELECT ?property ?name
            WHERE {
                ?thing td:hasPropertyAffordance ?property .
                ?property td:name ?name .
            }
            """
        )
    )

    return {str(row["property"]): str(row["name"]) for row in rows}


def all_interaction_effects(graph: Graph) -> list[tuple[str, str, Effect]]:
    results = []
    for affordance_type, predicate in (("property", TD.hasPropertyAffordance), ("action", TD.hasActionAffordance)):
        rows = list(
            graph.query(
                """
                PREFIX td: <https://www.w3.org/2019/wot/td#>

                SELECT ?affordance ?name
                WHERE {
                    ?thing ?predicate ?affordance .
                    ?affordance td:name ?name .
                }
                """,
                initBindings={"predicate": predicate},
            )
        )

        for row in rows:
            for effect in effects(graph, row["affordance"]):
                results.append((affordance_type, str(row["name"]), effect))

    return results


def preconditions(graph: Graph, affordance) -> list[Condition]:
    result = []
    for predicate in PRECONDITION_PREDICATES:
        for node in graph.objects(affordance, predicate):
            result.append(parse_condition(graph, node))

    return result


def effects(graph: Graph, affordance) -> list[Effect]:
    result = []
    for predicate in EFFECT_PREDICATES:
        for node in graph.objects(affordance, predicate):
            result.append(parse_effect(graph, node))

    return result


def parse_condition(graph: Graph, node) -> Condition:
    and_values = list(graph.objects(node, SPA["and"]))
    if and_values:
        return Condition("and", [parse_condition(graph, item) for item in list_values(graph, and_values[0])])

    numeric_equal_values = list(graph.objects(node, SPA["numeric-equal"]))
    if numeric_equal_values:
        return Condition("numeric-equal", [parse_value(graph, item) for item in list_values(graph, numeric_equal_values[0])])

    boolean_equal_values = list(graph.objects(node, SPA["boolean-equal"]))
    if boolean_equal_values:
        return Condition("boolean-equal", [parse_value(graph, item) for item in list_values(graph, boolean_equal_values[0])])

    raise PlanningError(f"Unsupported SPA condition node: {node}")


def parse_effect(graph: Graph, node) -> Effect:
    assign_values = list(graph.objects(node, SPA.assign))
    target_values = list(graph.objects(node, SPA.to))
    if len(assign_values) != 1 or len(target_values) != 1:
        raise PlanningError(f"SPA effect must contain one assign and one to: {node}")

    target = parse_reference(target_values[0])
    value = parse_value(graph, assign_values[0])
    return Effect(target=target.target, value=value)


def parse_value(graph: Graph, node):
    if isinstance(node, URIRef):
        return ValueRef(str(node))
    if isinstance(node, Literal):
        return node.toPython()
    if isinstance(node, BNode):
        numeric_add_values = list(graph.objects(node, SPA["numeric-add"]))
        if numeric_add_values:
            values = [parse_value(graph, item) for item in list_values(graph, numeric_add_values[0])]
            if len(values) != 2:
                raise PlanningError("spa:numeric-add requires exactly two operands")
            return NumericAdd(values[0], values[1])

    raise PlanningError(f"Unsupported SPA value node: {node}")


def parse_reference(node) -> ValueRef:
    if not isinstance(node, URIRef):
        raise PlanningError(f"Expected IRI reference, got: {node}")
    return ValueRef(str(node))


def list_values(graph: Graph, node) -> list:
    if (node, RDF.first, None) in graph:
        return list(Collection(graph, node))
    return list(graph.objects(node, RDF.first)) or list(graph.objects(node, RDF.value)) or [node]


def evaluate_value(value, state: dict[str, object], inputs: dict[str, object] | None = None):
    inputs = inputs or {}
    if isinstance(value, ValueRef):
        if value.target in state:
            return state[value.target]
        if value.target in inputs:
            return inputs[value.target]
        raise PlanningError(f"No known value for {value.target}")

    if isinstance(value, NumericAdd):
        return evaluate_value(value.left, state, inputs) + evaluate_value(value.right, state, inputs)

    return value


def condition_targets(condition: Condition) -> set[str]:
    if condition.kind == "and":
        result = set()
        for item in condition.args:
            result.update(condition_targets(item))
        return result

    result = set()
    for arg in condition.args:
        if isinstance(arg, ValueRef):
            result.add(arg.target)
    return result


def condition_satisfied(condition: Condition, state: dict[str, object]) -> bool:
    if condition.kind == "and":
        return all(condition_satisfied(item, state) for item in condition.args)

    if condition.kind in {"numeric-equal", "boolean-equal"}:
        if len(condition.args) != 2:
            raise PlanningError(f"{condition.kind} requires exactly two operands")
        try:
            left = evaluate_value(condition.args[0], state)
            right = evaluate_value(condition.args[1], state)
        except PlanningError:
            return False
        return left == right

    raise PlanningError(f"Unsupported SPA condition: {condition.kind}")


def effect_value(effect: Effect, state: dict[str, object], inputs: dict[str, object] | None = None):
    return evaluate_value(effect.value, state, inputs)
