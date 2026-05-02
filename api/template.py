from http.server import BaseHTTPRequestHandler

from shared import json_response, load_template


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            json_response(self, load_template())
        except Exception as error:
            json_response(self, {"error": str(error)}, status=500)
