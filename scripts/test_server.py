"""
test_server.py — Quick integration test for the ASR server.

Sends a synthetic silence PCM clip to the server's /recognize endpoint.

Usage:
    # Start server first:
    uvicorn server.app:app --host 0.0.0.0 --port 8080

    # Then run this test:
    python scripts/test_server.py [--host localhost] [--port 8080]
"""

from __future__ import annotations

import argparse
import struct
import sys
import urllib.request
import urllib.error
import json
import time

import numpy as np


def pcm_bytes(audio: np.ndarray) -> bytes:
    """Convert float32 array to 16-bit PCM bytes."""
    return (audio * 32767).astype(np.int16).tobytes()


def test_health(base_url: str) -> bool:
    try:
        req = urllib.request.Request(f"{base_url}/health")
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read())
            print(f"  /health: OK  |  backend={body.get('backend', '?')}")
            return True
    except Exception as exc:
        print(f"  /health: FAILED — {exc}")
        return False


def test_recognize(base_url: str, duration_s: float = 1.0) -> bool:
    sr = 16_000
    audio = np.zeros(int(sr * duration_s), dtype=np.float32)
    payload = pcm_bytes(audio)

    req = urllib.request.Request(
        f"{base_url}/recognize",
        data=payload,
        method="POST",
    )
    req.add_header("Content-Type", "application/octet-stream")
    req.add_header("X-Sample-Rate", "16000")
    req.add_header("X-Channels",    "1")
    req.add_header("X-Bit-Depth",   "16")

    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            body = json.loads(resp.read())
            print(f"  /recognize: OK  |  status={body.get('status')}  "
                  f"text='{body.get('text', '')}'  "
                  f"latency={body.get('duration_ms', '?')} ms  "
                  f"(round-trip: {elapsed_ms} ms)")
            return True
    except urllib.error.HTTPError as exc:
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        body = exc.read().decode()
        print(f"  /recognize: HTTP {exc.code} — {body}  ({elapsed_ms} ms)")
        return False
    except Exception as exc:
        print(f"  /recognize: FAILED — {exc}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Quick integration test for ASR server")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}"
    print(f"\nTesting ASR server at {base_url}\n")

    ok1 = test_health(base_url)
    ok2 = test_recognize(base_url)

    print()
    if ok1 and ok2:
        print("All tests passed.")
        sys.exit(0)
    else:
        print("Some tests FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    main()
