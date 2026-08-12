from urllib.request import Request, urlopen


def request(forms: dict, raw_bytes: bytes | None = None) -> bytes:
    method = forms["methodName"].upper()
    headers = {}
    if raw_bytes is not None:
        headers["Content-Type"] = forms["contentType"]

    request = Request(
        forms["target"],
        data=raw_bytes,
        method=method,
        headers=headers,
    )

    with urlopen(request, timeout=10) as response:
        body = response.read()

    return body


def get(forms: dict) -> bytes:
    return request(forms)


def put(forms: dict, raw_bytes: bytes) -> bytes:
    forms = dict(forms)
    forms["methodName"] = "PUT"
    return request(forms, raw_bytes)
