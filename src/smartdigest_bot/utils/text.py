from __future__ import annotations

import hashlib
import html


def normalize_whitespace(value: str) -> str:
    return " ".join(value.split())


def text_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def escape_html(value: str) -> str:
    return html.escape(value, quote=False)


def truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)].rstrip() + "…"
