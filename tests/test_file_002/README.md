# test_file_002

Tests local-file plain-text writing and readback.

It writes a string through `Thing.write("writeConfig")`, checks the file contents on disk, reads the value back through `Thing.read("readConfig")`, and restores the original fixture content afterward.
