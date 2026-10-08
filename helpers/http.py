"""Polite HTTP helpers: caching, retries with back-off, and friendly logging.

Why a cache?  A whole classroom usually shares ONE public IP address (campus NAT).
Keyless APIs such as Yahoo Finance and CoinGecko rate-limit *per IP*, so 30 students
re-running the same cell can trigger HTTP 429 for everyone. Caching successful
responses on disk means each URL is downloaded once, then re-used.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import time

import requests

# A realistic browser User-Agent. Yahoo's CDN rejects default library user agents.
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/140.0 Safari/537.36")

CACHE_DIR = pathlib.Path(__file__).resolve().parent.parent / "cache"
RETRY_STATUSES = {429, 500, 502, 503, 504}


class ApiError(RuntimeError):
    """Raised when an API answers with a non-success status."""

    def __init__(self, status: int, reason: str, url: str, body: str):
        self.status, self.reason, self.url, self.body = status, reason, url, body
        super().__init__(f"HTTP {status} {reason} for {url}\n{body[:300]}")


def _cache_path(url: str, params: dict | None, headers: dict | None) -> pathlib.Path:
    raw = json.dumps([url, params or {}, (headers or {}).get("Accept", "")], sort_keys=True)
    return CACHE_DIR / (hashlib.sha1(raw.encode()).hexdigest()[:20] + ".cache")


def fetch(url: str, params: dict | None = None, headers: dict | None = None,
          ttl: int = 900, kind: str = "json", retries: int = 3, verbose: bool = True):
    """GET a URL and return parsed JSON (kind="json") or text (kind="text").

    * Successful responses are cached on disk for `ttl` seconds.
    * 429 / 5xx responses are retried with exponential back-off, honouring Retry-After.
    * Any other non-2xx status raises ApiError so you can see what went wrong.
    """
    path = _cache_path(url, params, headers)
    if path.exists() and time.time() - path.stat().st_mtime < ttl:
        if verbose:
            print(f"⚡ cache hit   {url}")
        text = path.read_text(encoding="utf-8")
        return json.loads(text) if kind == "json" else text

    last = None
    for attempt in range(retries + 1):
        r = requests.get(url, params=params, headers=headers, timeout=20)
        last = r
        if verbose:
            ms = r.elapsed.total_seconds() * 1000
            print(f"{r.status_code} {r.reason:<18} {ms:6.0f} ms {len(r.content):>8,} bytes  {r.url[:80]}")
        if r.status_code in RETRY_STATUSES and attempt < retries:
            wait = r.headers.get("Retry-After")
            wait = float(wait) if wait and wait.isdigit() else 2 * 2 ** attempt
            if verbose:
                print(f"   ↻ server said {r.status_code}; waiting {wait:.0f}s then retrying…")
            time.sleep(wait)
            continue
        break

    if not last.ok:
        raise ApiError(last.status_code, last.reason, last.url, last.text)
    CACHE_DIR.mkdir(exist_ok=True)
    path.write_text(last.text, encoding="utf-8")
    return last.json() if kind == "json" else last.text


def show_response(r: requests.Response, body_chars: int = 400) -> None:
    """Pretty-print the parts of an HTTP response that matter when debugging."""
    print(f"Request : GET {r.request.url}")
    print(f"UA sent : {r.request.headers.get('User-Agent')}")
    print(f"Status  : {r.status_code} {r.reason}")
    print(f"Elapsed : {r.elapsed.total_seconds()*1000:.0f} ms")
    for h in ("Content-Type", "Content-Length", "Cache-Control", "ETag",
              "Retry-After", "X-RateLimit-Remaining"):
        if h in r.headers:
            print(f"{h:<15}: {r.headers[h]}")
    print("Body    :", r.text[:body_chars].replace("\n", " "), "…" if len(r.text) > body_chars else "")


def clear_cache() -> int:
    """Delete cached responses. Returns the number of files removed."""
    n = 0
    if CACHE_DIR.exists():
        for p in CACHE_DIR.glob("*.cache"):
            p.unlink()
            n += 1
    return n
