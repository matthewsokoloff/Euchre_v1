"""
Vercel serverless function: POST /api/game
Delegates all game logic to api/_utils.py.
"""
import json
import sys
import os
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api._utils import process_action  # noqa: E402


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body   = json.loads(self.rfile.read(length)) if length else {}
            result = process_action(body)
            blob   = json.dumps(result).encode()
            status = 200
        except Exception as exc:
            blob   = json.dumps({
                "error": str(exc),
                "state": None,
                "messages": [],
                "legal_cards": None,
            }).encode()
            status = 500

        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(blob)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, fmt, *args):  # suppress default access logs
        pass
