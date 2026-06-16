# test_http_005

Checks the WoT HTTP Binding default method for actions.

The TD contains an HTTP action form without `htv:methodName`. The runtime should
infer `POST` from the `invokeAction` operation and send the action input as
JSON.
