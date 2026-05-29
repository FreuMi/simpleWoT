# test_file_001

Tests local-file plain-text reading.

It loads a TD with a `file` target, reads `test_file` through `read_property("readConfig")`, decodes `text/plain`, and asserts the returned string matches the expected fixture content.
