"""
test_protocol.py — Tests for the ASR server communication protocol.

Tests: valid request framing, malformed input, end-of-command, response parsing.

Run with: pytest tests/test_protocol.py -v
"""

from __future__ import annotations

import json

import numpy as np
import pytest


# ──────────────────────────────────────────────────────
# Protocol helpers (mirrors server/protocol.py)
# ──────────────────────────────────────────────────────

SAMPLE_RATE = 16000
CHANNELS = 1
BIT_DEPTH = 16
CONTENT_TYPE = "application/octet-stream"


def make_audio_headers(sr: int = SAMPLE_RATE, ch: int = CHANNELS, bd: int = BIT_DEPTH) -> dict:
    """Construct HTTP headers for an audio stream request."""
    return {
        "Content-Type": CONTENT_TYPE,
        "X-Sample-Rate": str(sr),
        "X-Channels": str(ch),
        "X-Bit-Depth": str(bd),
    }


def validate_audio_headers(headers: dict) -> tuple[bool, str]:
    """
    Validate incoming request headers.
    Returns (ok, error_message).
    """
    required_keys = ["X-Sample-Rate", "X-Channels", "X-Bit-Depth", "Content-Type"]
    for key in required_keys:
        if key not in headers:
            return False, f"Missing header: {key}"

    if headers.get("Content-Type") != CONTENT_TYPE:
        return False, f"Expected Content-Type: {CONTENT_TYPE}"

    try:
        sr = int(headers["X-Sample-Rate"])
        if sr != SAMPLE_RATE:
            return False, f"Unexpected sample rate: {sr}"
    except ValueError:
        return False, "X-Sample-Rate must be integer"

    try:
        ch = int(headers["X-Channels"])
        if ch != CHANNELS:
            return False, f"Unexpected channels: {ch}"
    except ValueError:
        return False, "X-Channels must be integer"

    try:
        bd = int(headers["X-Bit-Depth"])
        if bd not in (16, 32):
            return False, f"Unsupported bit depth: {bd}"
    except ValueError:
        return False, "X-Bit-Depth must be integer"

    return True, ""


def audio_to_pcm_bytes(audio: np.ndarray) -> bytes:
    """Convert float32 audio array to 16-bit PCM bytes (little-endian)."""
    pcm = (audio * 32767).astype(np.int16)
    return pcm.tobytes()


def pcm_bytes_to_audio(data: bytes) -> np.ndarray:
    """Convert 16-bit PCM bytes back to float32 audio."""
    pcm = np.frombuffer(data, dtype=np.int16)
    return pcm.astype(np.float32) / 32767.0


def make_success_response(text: str, confidence: float = 1.0, duration_ms: int = 0) -> dict:
    return {"status": "ok", "text": text, "confidence": confidence, "duration_ms": duration_ms}


def make_error_response(code: str, message: str) -> dict:
    return {"status": "error", "code": code, "message": message}


# ──────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────

class TestAudioHeaders:
    def test_valid_headers(self):
        headers = make_audio_headers()
        ok, msg = validate_audio_headers(headers)
        assert ok, msg

    def test_missing_content_type(self):
        headers = {"X-Sample-Rate": "16000", "X-Channels": "1", "X-Bit-Depth": "16"}
        ok, msg = validate_audio_headers(headers)
        assert not ok
        assert "Content-Type" in msg

    def test_wrong_sample_rate(self):
        headers = make_audio_headers(sr=44100)
        ok, msg = validate_audio_headers(headers)
        assert not ok
        assert "sample rate" in msg.lower()

    def test_wrong_channels(self):
        headers = make_audio_headers(ch=2)
        ok, msg = validate_audio_headers(headers)
        assert not ok
        assert "channel" in msg.lower()

    def test_non_integer_sr(self):
        headers = make_audio_headers()
        headers["X-Sample-Rate"] = "not_a_number"
        ok, msg = validate_audio_headers(headers)
        assert not ok

    def test_unsupported_bit_depth(self):
        headers = make_audio_headers(bd=8)
        ok, msg = validate_audio_headers(headers)
        assert not ok

    def test_32bit_depth_accepted(self):
        headers = make_audio_headers(bd=32)
        ok, msg = validate_audio_headers(headers)
        assert ok, msg


class TestPcmEncoding:
    def test_round_trip(self):
        """float32 → PCM bytes → float32 should be close."""
        audio = np.array([0.0, 0.5, -0.5, 1.0, -1.0], dtype=np.float32)
        pcm = audio_to_pcm_bytes(audio)
        recovered = pcm_bytes_to_audio(pcm)
        np.testing.assert_allclose(audio, recovered, atol=1e-4)

    def test_silence_is_zero_bytes(self):
        audio = np.zeros(100, dtype=np.float32)
        pcm = audio_to_pcm_bytes(audio)
        assert all(b == 0 for b in pcm)

    def test_byte_length(self):
        """16-bit PCM: 2 bytes per sample."""
        audio = np.zeros(1000, dtype=np.float32)
        pcm = audio_to_pcm_bytes(audio)
        assert len(pcm) == 2000

    def test_empty_audio(self):
        audio = np.zeros(0, dtype=np.float32)
        pcm = audio_to_pcm_bytes(audio)
        assert len(pcm) == 0


class TestResponseFormat:
    def test_success_response_structure(self):
        resp = make_success_response("turn on the light", confidence=0.92, duration_ms=1234)
        assert resp["status"] == "ok"
        assert resp["text"] == "turn on the light"
        assert 0 <= resp["confidence"] <= 1.0
        assert resp["duration_ms"] >= 0

    def test_error_response_structure(self):
        resp = make_error_response("invalid_audio", "Expected 16000 Hz mono PCM")
        assert resp["status"] == "error"
        assert "code" in resp
        assert "message" in resp

    def test_success_response_is_json_serializable(self):
        resp = make_success_response("hello")
        try:
            json.dumps(resp)
        except TypeError:
            pytest.fail("Response is not JSON serializable")

    def test_error_response_is_json_serializable(self):
        resp = make_error_response("timeout", "Server did not respond")
        try:
            json.dumps(resp)
        except TypeError:
            pytest.fail("Error response is not JSON serializable")


class TestEndOfCommand:
    def test_max_duration_chunks(self):
        """
        Simulate chunked audio stream up to max command duration.
        Verify total bytes matches expected duration.
        """
        sr = 16000
        max_duration_s = 5
        chunk_size_s = 0.1
        max_chunks = int(max_duration_s / chunk_size_s)

        total_bytes = 0
        for _ in range(max_chunks):
            chunk = np.zeros(int(sr * chunk_size_s), dtype=np.float32)
            total_bytes += len(audio_to_pcm_bytes(chunk))

        expected_bytes = sr * max_duration_s * 2  # 2 bytes per sample
        assert total_bytes == expected_bytes
