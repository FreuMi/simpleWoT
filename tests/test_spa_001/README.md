# test_spa_001

Tests automatic SPA prerequisite execution from JSON-LD.

It invokes a target action with a boolean precondition. The runtime finds a prerequisite action with a matching SPA effect, executes it first, then executes the requested target action.
