# test_file_006

Tests local-file binary object writing and readback.

It writes a Python object through the byte-aligned binary encoder, verifies the raw bytes written to disk, reads the bytes back through `Thing.read("readConfig")`, and restores the placeholder fixture.
