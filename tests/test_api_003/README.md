# test_api_003

Checks operation-aware form selection.

The TD describes one property with separate `readproperty` and `writeproperty`
forms. The runtime should use the read form for `read_property()` and the write
form for `write_property()`.
