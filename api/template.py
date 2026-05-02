from http.server import BaseHTTPRequestHandler

from shared import json_response, load_template


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        json_response(self, load_template())
