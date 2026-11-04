"""Verified and idempotent model provisioner for the persistent Docker volume.

Only setup may download. The API mounts the same volume read-only and does not
attempt network downloads. Publish model and manifest atomically, in that order.
"""
import json
import os
import shutil
from pathlib import Path

from huggingface_hub import hf_hub_download
from app.services.model_manager import REPO, REV, SHA, NAME, SIZE, digest, verify

folder = Path(os.getenv("MODEL_DIR", "/models"))
folder.mkdir(parents=True, exist_ok=True)
target = folder / NAME
manifest = folder / "manifest.json"

if target.is_file() and target.stat().st_size == SIZE and digest(target) == SHA:
    print("Using previously verified Nemotron 3 Q8 GGUF from persistent volume.", flush=True)
else:
    print(f"Downloading pinned {REPO}@{REV} ({NAME})", flush=True)
    source = Path(hf_hub_download(repo_id=REPO, revision=REV, filename=NAME))
    if source.stat().st_size != SIZE or digest(source) != SHA:
        print("Hugging Face cache mismatch; retrying fresh download.", flush=True)
        source = Path(hf_hub_download(
            repo_id=REPO, revision=REV, filename=NAME, force_download=True
        ))
    if source.stat().st_size != SIZE or digest(source) != SHA:
        raise SystemExit("Downloaded GGUF size/SHA256 mismatch. Deployment refused.")
    staging = folder / (NAME + ".partial")
    try:
        shutil.copyfile(source, staging)
        if staging.stat().st_size != SIZE or digest(staging) != SHA:
            raise SystemExit("GGUF copy to Docker model volume failed integrity verification.")
        staging.chmod(0o644)
        os.replace(staging, target)
    finally:
        staging.unlink(missing_ok=True)

# The API runs as UID 10001; ensure the cached GGUF and manifest are readable.
target.chmod(0o644)
metadata = {"repo": REPO, "revision": REV, "sha256": SHA, "filename": NAME}
staging_manifest = folder / "manifest.json.partial"
try:
    staging_manifest.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    staging_manifest.chmod(0o644)
    os.replace(staging_manifest, manifest)
finally:
    staging_manifest.unlink(missing_ok=True)

verify(target, manifest)
print(f"Model READY: {target} and {manifest}; verified SHA256 {SHA}", flush=True)
