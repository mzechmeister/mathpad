#! /usr/bin/python3

PORT = 8003
BASE_DIR = "data"
MAX_EDIT_SIZE = 1 * 1024 * 1024   # 1 MB
ALLOWED_EXT = {".txt", ".md", ".json", ".csv", ".py"}

import os
import http.server
import socketserver
import urllib
import json

os.makedirs(BASE_DIR, exist_ok=True)

class Handler(http.server.SimpleHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
    def _safe_path(self, name):
        ext = os.path.splitext(name)[1].lower()
        if ext not in ALLOWED_EXT:
            return None
        return os.path.join(BASE_DIR, name)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Access-Control-Allow-Methods", "DELETE, GET, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/list":
            files = []
            for entry in sorted(os.listdir(BASE_DIR)):
                p = os.path.join(BASE_DIR, entry)
                if os.path.isfile(p) and os.path.splitext(entry)[1].lower() in ALLOWED_EXT:
                    st = os.stat(p)
                    files.append({"name": entry, "size": st.st_size, "mtime": int(st.st_mtime)})
            data = json.dumps(files).encode("utf-8")
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if parsed.path == "/files":
            qs = urllib.parse.parse_qs(parsed.query)
            name = qs.get("name", [None])[0]
            print("files", name)
            path = self._safe_path(name)
            if not path:
                msg = b"Invalid filename or extension"
                self.send_response(400)
                self._cors()
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(msg)))
                self.end_headers()
                self.wfile.write(msg)
                return
            if not os.path.exists(path):
                msg = b"Not found"
                self.send_response(404)
                self._cors()
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(msg)))
                self.end_headers()
                self.wfile.write(msg)
                return
            with open(path, "rb") as f:
                data = f.read(MAX_EDIT_SIZE + 1)
            if len(data) > MAX_EDIT_SIZE:
                msg = b"File too large"
                self.send_response(413)
                self._cors()
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(msg)))
                self.end_headers()
                self.wfile.write(msg)
                return
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                msg = b"File is not valid UTF-8"
                self.send_response(415)
                self._cors()
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(msg)))
                self.end_headers()
                self.wfile.write(msg)
                return
            body = text.encode("utf-8")
            st = os.stat(path)
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Last-Modified", self.date_time_string(st.st_mtime))
            self.end_headers()
            self.wfile.write(body)
            return

        return super().do_GET()  # static files (e.g. index.html)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/files":
            self.send_response(404)
            self._cors()
            self.end_headers()
            self.wfile.write(b"Not found")
            return

        qs = urllib.parse.parse_qs(parsed.query)
        name = qs.get("name", [None])[0]
        path = self._safe_path(name)
        if not path:
            msg = b"Invalid filename or extension"
            self.send_response(400)
            self._cors()
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_EDIT_SIZE:
            msg = f"Bad size (got {length}, max {MAX_EDIT_SIZE})".encode("utf-8")
            self.send_response(413 if length > MAX_EDIT_SIZE else 400)
            self._cors()
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)
            return

        data = self.rfile.read(length)
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            msg = b"Body must be UTF-8 text"
            self.send_response(415)
            self._cors()
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)
            return

        created = not os.path.exists(path)
        print(data)
        with open(path, "wb") as f:
            f.write(data)

        resp = json.dumps({"saved": name, "created": created, "size": len(data)}).encode("utf-8")
        self.send_response(201 if created else 200)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(resp)))
        self.end_headers()
        self.wfile.write(resp)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/files":
            self.send_response(404)
            self._cors()
            self.end_headers()
            self.wfile.write(b"Not found")
            return

        qs = urllib.parse.parse_qs(parsed.query)
        name = qs.get("name", [None])[0]
        path = self._safe_path(name)
        if not path:
            msg = b"Invalid filename or extension"
            self.send_response(400)
            self._cors()
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)
            return

        existed = os.path.exists(path)
        if existed:
            os.remove(path)

        resp = json.dumps({"deleted": name, "existed": existed}).encode("utf-8")
        self.send_response(200 if existed else 201)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(resp)))
        self.end_headers()
        self.wfile.write(resp)

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Server running on http://0.0.0.0:{PORT}, data folder ./{BASE_DIR}")
        httpd.serve_forever()
