# test_file_003

Tests local-file JSON reading.

It reads a JSON fixture through `Thing.read("readConfig")`, uses the `application/json` codec, and asserts the returned Python dictionary matches the expected data.
