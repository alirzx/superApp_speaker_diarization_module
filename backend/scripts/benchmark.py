"""Measure round-trip CPU API time for one locally supplied recording."""
import argparse
import os
import time
import httpx

parser = argparse.ArgumentParser()
parser.add_argument("file")
parser.add_argument("--url", default=os.getenv("API_URL", "http://127.0.0.1:8003"))
parser.add_argument("--token", default=os.getenv("API_TOKEN", ""))
args = parser.parse_args()

with open(args.file, "rb") as audio:
    started = time.perf_counter()
    response = httpx.post(
        args.url.rstrip("/") + "/v1/diarize",
        files={"file": (os.path.basename(args.file), audio)},
        headers={"X-API-Key": args.token} if args.token else {},
        timeout=900,
    )
    response.raise_for_status()
    print({
        "wall_seconds": round(time.perf_counter() - started, 3),
        "response": response.json(),
    })
