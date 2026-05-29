# test_api_002

Tests WoT-style action invocation.

It calls `invoke_action()` on an action affordance with an input `const`, verifies the runtime encodes that constant as binary data, and checks the bytes written to the local file target.
