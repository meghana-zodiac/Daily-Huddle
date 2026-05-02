from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler

from shared import fetch_submissions, insert_submission, json_response, normalize_text, read_json_body


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            json_response(self, fetch_submissions())
        except Exception as error:
            json_response(self, {"error": str(error)}, status=502)

    def do_POST(self):
        try:
            payload = read_json_body(self)
            employee_name = normalize_text(payload.get("employeeName"))
            entry_date = normalize_text(payload.get("entryDate"))
            values = payload.get("values") or {}
            notes = normalize_text(payload.get("notes"))

            if not employee_name:
                json_response(self, {"error": "Employee name is required."}, status=400)
                return
            if not entry_date:
                json_response(self, {"error": "Entry date is required."}, status=400)
                return

            now_utc = datetime.now(UTC)
            submission = {
                "id": f"entry-{now_utc.strftime('%Y%m%d%H%M%S%f')}",
                "employeeName": employee_name,
                "entryDate": entry_date,
                "notes": notes,
                "submittedAt": now_utc.isoformat(timespec="seconds").replace("+00:00", "Z"),
                "values": values,
            }
            json_response(self, {"ok": True, "submission": insert_submission(submission)}, status=201)
        except Exception as error:
            json_response(self, {"error": str(error)}, status=502)
