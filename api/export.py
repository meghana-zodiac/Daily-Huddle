from datetime import date
from http.server import BaseHTTPRequestHandler

from api.shared import build_csv, fetch_submissions, text_response


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            filename = f'daily-huddle-submissions-{date.today().isoformat()}.csv'
            text_response(
                self,
                build_csv(fetch_submissions()),
                "text/csv; charset=utf-8",
                extra_headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
        except Exception as error:
            text_response(self, str(error), "text/plain; charset=utf-8", status=502)
