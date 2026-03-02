from urllib.request import urlopen

def get(forms: dict) -> bytes:
    url = forms["target"]
    print(url)

    with urlopen(url, timeout=10) as response:
        body = response.read()

    return body