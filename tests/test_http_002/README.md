# test_http_002

Tests HTTP JSON writing.

It starts a local in-process HTTP server, generates a temporary TD pointing at that server, writes JSON through `Thing.write("writeConfig")`, and asserts the server received a `PUT /config` request with the expected content type and body.
