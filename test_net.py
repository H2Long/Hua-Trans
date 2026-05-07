#!/usr/bin/env python3
"""Quick network test for Google Translate API."""
import urllib.request
import urllib.parse
import json
import time

url = "https://translate.googleapis.com/translate_a/single"
params = urllib.parse.urlencode({
    "client": "gtx",
    "sl": "en",
    "tl": "zh",
    "dt": "t",
    "q": "Hello",
})

print("Testing Google Translate API...")
start = time.time()
try:
    req = urllib.request.Request(
        f"{url}?{params}",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    elapsed = time.time() - start
    result = data[0][0][0]
    print(f"OK: {result} ({elapsed:.1f}s)")
except Exception as e:
    elapsed = time.time() - start
    print(f"FAIL: {e} ({elapsed:.1f}s)")
