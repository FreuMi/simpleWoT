def read(forms: dict) -> bytes:
    file_path = forms["target"]

    if file_path.startswith("file://"):
        file_path = file_path.split("file://")[1]

    with open(file_path, 'rb') as f:
        file_bytes = f.read()

    return file_bytes


def write(forms: dict, data: bytes) -> int:
    file_path = forms["target"]

    if file_path.startswith("file://"):
        file_path = file_path.split("file://")[1]

    with open(file_path, 'wb') as f:
        bytes_written = f.write(data)
