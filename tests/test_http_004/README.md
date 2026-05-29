# test_http_004

Checks that explicit TD HTTP method annotations override WoT defaults.

The TD contains a writable property form with `htv:methodName` set to `POST`.
Although `writeProperty` defaults to `PUT`, the runtime must use the annotated
`POST` method.
