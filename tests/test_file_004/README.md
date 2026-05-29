# test_file_004

Tests local-file JSON writing and readback.

It writes a Python dictionary through `write_property("writeConfig")`, verifies the file parses to the expected JSON object, reads it back through `read_property("readConfig")`, and restores the original fixture.
