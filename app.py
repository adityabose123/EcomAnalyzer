"""Local web app: python app.py  ->  open http://localhost:8000 and click Run. Stdlib server + Playwright."""
import json, threading, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import garnier_products as G

ROOT = Path(__file__).parent
DATA_FILE = ROOT / "data.json"
S = {"running": False, "log": [], "stop": False, "data": None}
LOCK = threading.Lock()


def log(msg):
    with LOCK:
        S["log"].append(msg); S["log"] = S["log"][-300:]


def load():
    if S["data"] is None and DATA_FILE.exists():
        S["data"] = json.loads(DATA_FILE.read_text())
    return S["data"]


def on_data(d):
    S["data"] = json.loads(json.dumps(d))
    DATA_FILE.write_text(json.dumps(d, ensure_ascii=False))


def worker(opts):
    try:
        from scraper import run_scrape  # imported lazily so the UI starts even if Playwright is missing
        d = run_scrape(opts, log, on_data, lambda: S["stop"])
        on_data(d); log("Done.")
    except Exception as e:
        log(f"ERROR: {e}")
    finally:
        S["running"] = False


class H(BaseHTTPRequestHandler):
    def send(self, body, ctype="application/json", code=200):
        b = body if isinstance(body, bytes) else body.encode()
        self.send_response(code); self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        if self.path == "/":
            html = (ROOT / "dashboard_template.html").read_text().replace("/*__DATA__*/null", "null")
            self.send(html, "text/html")
        elif self.path == "/api/state":
            self.send(json.dumps({"running": S["running"], "log": S["log"][-40:], "data": load(),
                                  "products": [{"key": p[0], "name": p[1]} for p in G.PRODUCTS]}))
        else:
            self.send("not found", "text/plain", 404)

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(n) or b"{}")
        if self.path == "/api/run" and not S["running"]:
            o = {"domain": body.get("domain") or "amazon.in", "pages": int(body.get("pages") or 3),
                 "tolerance": float(body.get("tolerance") or 40), "max_competitors": int(body.get("max_competitors") or 8),
                 "products": body.get("products") or None, "headful": bool(body.get("headful", True))}
            S.update(running=True, stop=False, log=[]); log("Starting…")
            threading.Thread(target=worker, args=(o,), daemon=True).start()
        elif self.path == "/api/stop":
            S["stop"] = True; log("Stopping after the current page…")
        self.send(json.dumps({"ok": True}))

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", 8000), H)
    print("Open http://localhost:8000"); webbrowser.open("http://localhost:8000")
    srv.serve_forever()
