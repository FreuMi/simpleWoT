# test_http_003

Checks the WoT HTTP Binding default method for property writes.

The TD contains a writable HTTP property form without `htv:methodName`. The
runtime should infer `PUT` from the `writeProperty` operation and send the JSON
body to the local test server.
