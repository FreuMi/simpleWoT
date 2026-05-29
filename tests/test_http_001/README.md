# test_http_001

Tests HTTP JSON reading.

It starts a local in-process HTTP server, generates a temporary TD pointing at that server, reads `GET /config` through `read_property("readConfig")`, and asserts the decoded JSON object.
