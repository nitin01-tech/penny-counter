"""Serve Penny Counter and persist the same expenses.json format as expense_track.py."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
DATA_FILE = HERE / "expenses.json"
HTML_FILE = HERE / "penny-counter.html"

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(HERE), **kwargs)

    def do_GET(self):
        if self.path == "/api/data":
            if DATA_FILE.exists():
                try:
                    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
                    if not isinstance(data, dict) or not isinstance(data.get("current"), dict):
                        raise ValueError("Invalid tracker data")
                except (OSError, json.JSONDecodeError, ValueError):
                    self.send_error(500, "Could not read expenses.json")
                    return
            else:
                data = None
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path in ("/", "/penny-counter.html"):
            self.path = "/penny-counter.html"
        return super().do_GET()

    def do_POST(self):
        if self.path != "/api/data":
            self.send_error(404)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size <= 0 or size > 5_000_000:
                raise ValueError("Invalid request size")
            data = json.loads(self.rfile.read(size).decode("utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("current"), dict) or not isinstance(data.get("history"), list):
                raise ValueError("Expected current and history data")
            current = data["current"]
            if not isinstance(current.get("expenses", []), list) or not isinstance(current.get("starting_balance", 0), (int, float)):
                raise ValueError("Invalid month data")
            temp = DATA_FILE.with_suffix(".json.tmp")
            temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            temp.replace(DATA_FILE)
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError, OSError) as exc:
            self.send_error(400, str(exc))
            return
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

if __name__ == "__main__":
    print("Penny Counter is running at http://127.0.0.1:8000")
    print(f"Using expense data: {DATA_FILE}")
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
