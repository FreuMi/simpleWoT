import asyncio
import json
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from simplewot import Thing


WRITE_DATA = {
    "name": "simpleWoT",
    "transport": "http",
    "enabled": False,
    "count": 2,
}
REQUESTS = []


class Handler(BaseHTTPRequestHandler):
    def do_PUT(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)
        REQUESTS.append(
            {
                "method": self.command,
                "path": self.path,
                "content_type": self.headers.get("Content-Type"),
                "body": body,
            }
        )

        response = b"{}"
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, format, *args):
        pass


def write_runtime_td(test_dir: Path, href: str) -> Path:
    td = json.loads((test_dir / "td.json").read_text(encoding="utf-8"))
    td["properties"]["writeConfig"]["forms"][0]["href"] = href

    temp_file = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    with temp_file:
        json.dump(td, temp_file)

    return Path(temp_file.name)


async def main():
    test_dir = Path(__file__).resolve().parent
    REQUESTS.clear()

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    runtime_td = write_runtime_td(test_dir, f"http://127.0.0.1:{server.server_port}/config")
    thing = Thing(str(runtime_td))

    try:
        await thing.write("writeConfig", WRITE_DATA)

        assert len(REQUESTS) == 1, f"Expected one request, got {len(REQUESTS)}"
        request = REQUESTS[0]
        assert request["method"] == "PUT", f"Expected PUT, got {request['method']}"
        assert request["path"] == "/config", f"Expected /config, got {request['path']}"
        assert request["content_type"] == "application/json", (
            f"Expected application/json, got {request['content_type']}"
        )
        assert json.loads(request["body"].decode("utf-8")) == WRITE_DATA
    finally:
        await thing.cleanup()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        runtime_td.unlink(missing_ok=True)


if __name__ == "__main__":
    asyncio.run(main())
