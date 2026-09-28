"""
protocol.py — Response formatting for the ASR server protocol.
"""

from __future__ import annotations

import time
from typing import Optional


def success_response(text: str, confidence: Optional[float], duration_ms: int) -> dict:
    return {
        "status": "ok",
        "text": text,
        "confidence": confidence,
        "duration_ms": duration_ms,
    }


def error_response(code: str, message: str) -> dict:
    return {
        "status": "error",
        "code": code,
        "message": message,
    }
