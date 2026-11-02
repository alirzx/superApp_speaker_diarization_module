"""Health smoke test against the selected host port."""
import os
import urllib.request

base = os.getenv("API_URL", "http://127.0.0.1:8003").rstrip("/")
for path in ("/health/live", "/health/ready"):
    with urllib.request.urlopen(base + path, timeout=10) as response:
        print(path, response.status, response.read().decode())
