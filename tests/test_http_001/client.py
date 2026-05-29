import asyncio
import json
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from simplewot import Thing


EXPECTED_DATA = {
    "name": "simpleWoT",
    "transport": "http",
    "enabled": True,
}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        assert self.path == "/config", f"Expected /config, got {self.path}"

        body = json.dumps(EXPECTED_DATA).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


def write_runtime_td(test_dir: Path, href: str) -> Path:
    td = json.loads((test_dir / "td.json").read_text(encoding="utf-8"))
    td["properties"]["readConfig"]["forms"][0]["href"] = href

    temp_file = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    with temp_file:
        json.dump(td, temp_file)

    return Path(temp_file.name)


async def main():
    test_dir = Path(__file__).resolve().parent
    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    runtime_td = write_runtime_td(test_dir, f"http://127.0.0.1:{server.server_port}/config")
    thing = Thing(str(runtime_td))

    try:
        data = await thing.read("readConfig")
        assert data == EXPECTED_DATA, f"Expected {EXPECTED_DATA!r}, got {data!r}"
    finally:
        await thing.cleanup()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        runtime_td.unlink(missing_ok=True)


if __name__ == "__main__":
    asyncio.run(main())
