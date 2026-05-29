# test_spa_002

Tests automatic SPA precondition satisfaction from a Turtle TD.

It proves SPA parsing is RDF-serialization independent by using Turtle. The runtime reads a property to populate state, sees that the target action precondition is already satisfied, and invokes only the target action.
