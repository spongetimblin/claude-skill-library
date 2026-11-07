#!/usr/bin/env python3
"""Receive one form POST from panel_extract.js and save its text.

  python3 -I receive_post.py OUT_FILE      (run in the background, then run the JS)

Listens on 127.0.0.1:8765 only, accepts a single POST, and exits. Gives up after
300 seconds with no request.
"""
import http.server
import sys
import urllib.parse

OUT = sys.argv[1]


class Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"])).decode("utf-8")
        text = urllib.parse.parse_qs(body, keep_blank_values=True).get("t", [""])[0]
        with open(OUT, "w", encoding="utf-8") as f:
            f.write(text.replace("\r", ""))
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Transcript saved. You can close this tab.")
        print(f"saved {len(text)} characters to {OUT}", flush=True)

    def log_message(self, *args):
        pass


server = http.server.HTTPServer(("127.0.0.1", 8765), Handler)
server.timeout = 300
server.handle_request()
