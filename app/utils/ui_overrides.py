import os
import json
from typing import Optional

_cache = None
_path = os.path.join("app", "data", "ui_overrides.json")

def _load() -> dict:
    global _cache
    if _cache is not None:
        return _cache
    if os.path.exists(_path):
        try:
            with open(_path, "r", encoding="utf-8") as f:
                _cache = json.load(f) or {}
        except Exception:
            _cache = {}
    else:
        _cache = {}
    return _cache


def get_rating_panel_html() -> Optional[str]:
    data = _load()
    val = data.get("rating_panel_html")
    return val if isinstance(val, str) and val.strip() else None


def get_instructions_html() -> Optional[str]:
    data = _load()
    val = data.get("instructions_html")
    return val if isinstance(val, str) and val.strip() else None


def get_email_templates() -> dict:
    data = _load()
    return {
        "employee_subject": (data.get("employee_email_subject") or "").strip(),
        "employee_html": (data.get("employee_email_html") or "").strip(),
        "supervisor_subject": (data.get("supervisor_email_subject") or "").strip(),
        "supervisor_html": (data.get("supervisor_email_html") or "").strip(),
    }

