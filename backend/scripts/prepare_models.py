"""One-shot, idempotent, pinned model provisioning into the shared Docker volume.

An existing valid GGUF needs no network and is never redownloaded. Downloads
are verified before atomic installation. Manifest is the last file published.
"""
import json
import os
import shutil
from pathlib import Path
from huggingface_hub import hf_hub_download

from app.services.model_manager import REV, SHA, NAME, digest, verify

folder = Path(os.getenv("MODEL_DIR", "/models"))
folder.mkdir(parents=True, exist_ok=True)
target = folder / NAME
manifest = folder / "manifest.json"

if target.is_file() and digest(target) == SHA:
    print("Cached Nemotron 3 Q8 GGUF verified; skipping download.", flush=True)
else:
    print("Preparing pinned Nemotron 3 Q8 GGUF from Hugging Face...", flush=True)
    source = Path(hf_hub_download(
        repo_id="nvidia/Nemotron-3-Diarization", revision=REV, filename=NAME
    ))
    if digest(source) != SHA:
        print("Hugging Face cache checksum mismatch: retrying a fresh download.", flush=True)
        source = Path(hf_hub_download(
            repo_id="nvidia/Nemotron-3-Diarization", revision=REV,
            filename=NAME, force_download=True
        ))
    if digest(source) != SHA:
        raise SystemExit("Model download SHA256 mismatch; refusing deployment.")
    staging = folder / (NAME + ".partial")
    try:
        shutil.copyfile(source, staging)
        if digest(staging) != SHA:
            raise SystemExit("Model copied to volume failed SHA256.")
        os.replace(staging, target)
    finally:
        staging.unlink(missing_ok=True)

new_manifest = {"repo": "nvidia/Nemotron-3-Diarization", "revision": REV,
                "sha256": SHA, "filename": NAME}
staging_manifest = folder / "manifest.json.partial"
try:
    staging_manifest.write_text(json.dumps(new_manifest, indent=2) + "\n", encoding="utf-8")
    os.replace(staging_manifest, manifest)
finally:
    staging_manifest.unlink(missing_ok=True)

verify(target, manifest)
print("Nemotron 3 ready in persistent /models volume (model and manifest verified).", flush=True)
