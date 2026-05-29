# test_file_005

Tests local-file binary decoding.

It writes known fixture bytes to `test_file`, reads them with `application/x.binary-data-stream`, and verifies the binary codec decodes temperature, humidity, and voltage fields using the TD bit metadata.
