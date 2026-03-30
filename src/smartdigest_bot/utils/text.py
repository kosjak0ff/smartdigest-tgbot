from __future__ import annotations

import hashlib
import html
import re


def normalize_whitespace(value: str) -> str:
    return " ".join(value.split())


def normalize_message_text(value: str) -> str:
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in value.replace("\r\n", "\n").split("\n")]
    normalized: list[str] = []
    previous_blank = False
    for line in lines:
        if not line:
            if not previous_blank and normalized:
                normalized.append("")
            previous_blank = True
            continue
        normalized.append(line)
        previous_blank = False
    return "\n".join(normalized).strip()


def text_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def escape_html(value: str) -> str:
    return html.escape(value, quote=False)


def truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)].rstrip() + "…"
