from urllib.request import Request, urlopen

def get(forms: dict) -> bytes:
    url = forms["target"]

    with urlopen(url, timeout=10) as response:
        body = response.read()

    return body


def put(forms: dict, raw_bytes: bytes) -> bytes:
    request = Request(
        forms["target"],
        data=raw_bytes,
        method="PUT",
        headers={"Content-Type": forms["contentType"]},
    )

    with urlopen(request, timeout=10) as response:
        body = response.read()

    return body
