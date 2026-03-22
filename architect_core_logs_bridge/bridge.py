import json
import os
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer


HOST = "0.0.0.0"
PORT = 8099


def fetch_core_logs(lines: int) -> tuple[int, str, str]:
    token = os.environ.get("SUPERVISOR_TOKEN", "").strip()

    if not token:
        return 500, "text/plain", "SUPERVISOR_TOKEN is missing"

    if lines < 1:
        lines = 1
    if lines > 5000:
        lines = 5000

    url = f"http://supervisor/core/logs/latest?lines={lines}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, "text/plain; charset=utf-8", body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, "text/plain; charset=utf-8", body
    except Exception as exc:
        return 500, "text/plain; charset=utf-8", f"Unexpected error: {exc!r}"


class Handler(BaseHTTPRequestHandler):
    def _send_text(self, status: int, body: str, content_type: str = "text/plain; charset=utf-8"):
        encoded = body.encode("utf-8", errors="replace")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_json(self, status: int, payload: dict):
        body = json.dumps(payload)
        self._send_text(status, body, "application/json; charset=utf-8")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/health":
            self._send_json(
                200,
                {
                    "status": "ok",
                    "service": "architect_core_logs_bridge",
                    "port": PORT,
                },
            )
            return

        if parsed.path == "/core-logs/latest":
            params = urllib.parse.parse_qs(parsed.query)
            raw_lines = params.get("lines", ["200"])[0]

            try:
                lines = int(raw_lines)
            except ValueError:
                self._send_json(400, {"error": "lines must be an integer"})
                return

            status, content_type, body = fetch_core_logs(lines)
            self._send_text(status, body, content_type)
            return

        self._send_json(404, {"error": "Not found"})

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    print(f"Starting Architect Core Logs Bridge on {HOST}:{PORT}")
    server = HTTPServer((HOST, PORT), Handler)
    server.serve_forever()
