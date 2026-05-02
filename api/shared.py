from __future__ import annotations

import csv
import json
import os
from io import StringIO
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = BASE_DIR / "data" / "template.json"
TABLE_NAME = "daily_huddle_entries"
FIELD_COLUMN_MAP = {
    "monthly-revenue-value-2": {
        "left": "monthly_revenue_value_target",
        "right": "monthly_revenue_value_achieved_pipeline",
    },
    "monthly-revenue-number-3": {
        "left": "monthly_revenue_number_target",
        "right": "monthly_revenue_number_achieved_pipeline",
    },
    "monthly-revenue-achieved-4": {
        "left": "monthly_revenue_achieved_percent_target",
        "right": "monthly_revenue_achieved_percent_actual",
    },
    "monthly-booking-value-7": {
        "left": "monthly_booking_value_high",
        "right": "monthly_booking_value_medium",
    },
    "monthly-booking-number-8": {
        "left": "monthly_booking_number_high",
        "right": "monthly_booking_number_medium",
    },
    "monthly-booking-total-value-number-9": {
        "left": "monthly_booking_total_value",
        "right": "monthly_booking_total_number",
    },
    "daily-activity-1-yesterday-s-poa-cv-12": {
        "left": "yesterdays_poa_target",
        "right": "yesterdays_poa_achieved",
    },
    "daily-activity-1-mtd-poa-cv-13": {
        "left": "mtd_poa_target",
        "right": "mtd_poa_achieved",
    },
    "daily-activity-1-yesterday-s-initial-interview-14": {
        "left": "yesterdays_initial_interview_target",
        "right": "yesterdays_initial_interview_achieved",
    },
    "daily-activity-1-yesterday-s-final-interview-15": {
        "left": "yesterdays_final_interview_target",
        "right": "yesterdays_final_interview_achieved",
    },
    "daily-activity-1-mtd-initial-interview-16": {
        "left": "mtd_initial_interview_target",
        "right": "mtd_initial_interview_achieved",
    },
    "daily-activity-1-mtd-final-interview-17": {
        "left": "mtd_final_interview_target",
        "right": "mtd_final_interview_achieved",
    },
    "daily-activity-1-total-interviews-till-date-18": {
        "left": "total_interviews_target",
        "right": "total_interviews_achieved",
    },
}


def load_template() -> dict[str, Any]:
    return json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))


def json_response(handler, payload: Any, status: int = 200) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def text_response(handler, payload: str, content_type: str, status: int = 200, extra_headers: dict[str, str] | None = None) -> None:
    body = payload.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    for key, value in (extra_headers or {}).items():
        handler.send_header(key, value)
    handler.end_headers()
    handler.wfile.write(body)


def read_json_body(handler) -> Any:
    content_length = int(handler.headers.get("Content-Length", "0"))
    raw_body = handler.rfile.read(content_length)
    return json.loads(raw_body.decode("utf-8"))


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def require_env(name: str) -> str:
    value = normalize_text(os.environ.get(name))
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def supabase_request(method: str, path: str, *, query: dict[str, str] | None = None, json_body: Any | None = None) -> Any:
    base_url = require_env("SUPABASE_URL").rstrip("/")
    service_role_key = require_env("SUPABASE_SERVICE_ROLE_KEY")
    query_string = f"?{urlencode(query)}" if query else ""
    url = f"{base_url}/rest/v1/{path}{query_string}"
    body = None if json_body is None else json.dumps(json_body).encode("utf-8")
    headers = {
        "apikey": service_role_key,
        "Authorization": f"Bearer {service_role_key}",
        "Accept": "application/json",
    }
    if body is not None:
        headers["Content-Type"] = "application/json"

    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=15) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Supabase request failed with {error.code}: {details}") from error
    except URLError as error:
        raise RuntimeError(f"Could not reach Supabase: {error.reason}") from error


def map_submission_to_row(submission: dict[str, Any]) -> dict[str, Any]:
    template = load_template()
    row = {
        "id": submission["id"],
        "employee_name": submission["employeeName"],
        "entry_date": submission["entryDate"],
        "notes": submission.get("notes", ""),
        "submitted_at": submission["submittedAt"],
        "workbook_name": template["workbookName"],
        "sheet_name": template["sheetName"],
        "values": submission["values"],
    }
    for field_key, column_map in FIELD_COLUMN_MAP.items():
        values = submission["values"].get(field_key) or {}
        row[column_map["left"]] = values.get("left")
        row[column_map["right"]] = values.get("right")
    return row


def map_row_to_submission(row: dict[str, Any]) -> dict[str, Any]:
    values = row.get("values") or {}
    for field_key, column_map in FIELD_COLUMN_MAP.items():
        values[field_key] = {
            "left": row.get(column_map["left"]),
            "right": row.get(column_map["right"]),
        }
    return {
        "id": row["id"],
        "employeeName": row.get("employee_name", ""),
        "entryDate": row.get("entry_date", ""),
        "notes": row.get("notes", ""),
        "submittedAt": row.get("submitted_at", ""),
        "values": values,
    }


def fetch_submissions() -> list[dict[str, Any]]:
    rows = supabase_request(
        "GET",
        TABLE_NAME,
        query={"select": "*", "order": "submitted_at.desc"},
    )
    return [map_row_to_submission(row) for row in (rows or [])]


def insert_submission(submission: dict[str, Any]) -> dict[str, Any]:
    result = supabase_request(
        "POST",
        TABLE_NAME,
        query={"select": "*"},
        json_body=map_submission_to_row(submission),
    )
    if not result:
        return submission
    return map_row_to_submission(result[0])


def build_csv(submissions: list[dict[str, Any]]) -> str:
    template = load_template()
    field_map: dict[str, tuple[str, list[str]]] = {}
    for section in template["sections"]:
        headers = section["headers"]
        for field in section["fields"]:
            field_map[field["key"]] = (field["label"], headers)

    flattened: list[dict[str, Any]] = []
    for submission in submissions:
        row: dict[str, Any] = {
            "id": submission["id"],
            "employeeName": submission["employeeName"],
            "entryDate": submission["entryDate"],
            "submittedAt": submission["submittedAt"],
            "notes": submission.get("notes", ""),
        }
        for field_key, values in submission["values"].items():
            label, headers = field_map.get(field_key, (field_key, ["Value 1", "Value 2"]))
            row[f"{label} - {headers[0]}"] = values.get("left")
            row[f"{label} - {headers[1]}"] = values.get("right")
        flattened.append(row)

    if not flattened:
        return "id,employeeName,entryDate,submittedAt,notes\r\n"

    headers: list[str] = []
    for row in flattened:
        for key in row:
            if key not in headers:
                headers.append(key)

    stream = StringIO()
    writer = csv.DictWriter(stream, fieldnames=headers)
    writer.writeheader()
    writer.writerows([{header: row.get(header, "") for header in headers} for row in flattened])
    return stream.getvalue()
