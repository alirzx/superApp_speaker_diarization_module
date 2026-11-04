"""Strict, explainable verification for the pinned Nemotron-3 GGUF cache.

The API is intentionally offline. Only the one-shot model-setup service may
download model files. A missing or corrupt artifact fails closed at startup.
"""
import hashlib
import json
from pathlib import Path

REPO = "nvidia/Nemotron-3-Diarization"
REV = "f667ed73aee57d40cc39428eb768b4fd87a0a29e"
SHA = "08456d9e22cd9a323c0364d98375f3746d6e68507ebb705cd46438c534c7a3a1"
NAME = "Nemotron-3-Diarization.q8_0.gguf"
SIZE = 107012128

class ModelPreparationError(RuntimeError):
    """Model volume not prepared or the pinned artifacts failed validation."""

def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def verify(path, manifest):
    model_path = Path(path)
    manifest_path = Path(manifest)
    advice = "Check 'docker compose logs model-setup' and the shared model_cache volume."
    if not manifest_path.is_file():
        raise ModelPreparationError(f"Model manifest missing: {manifest_path}. {advice}")
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ModelPreparationError(f"Model manifest unreadable/invalid: {manifest_path}. {advice}") from exc
    if not isinstance(data, dict) or any((
        data.get("repo") != REPO,
        data.get("revision") != REV,
        data.get("sha256") != SHA,
        data.get("filename") != NAME,
        model_path.name != NAME,
    )):
        raise ModelPreparationError(f"Model manifest identity mismatch: {manifest_path}. {advice}")
    if not model_path.is_file():
        raise ModelPreparationError(f"Model GGUF missing: {model_path}. {advice}")
    try:
        actual_size = model_path.stat().st_size
        if actual_size != SIZE:
            raise ModelPreparationError(
                f"Model GGUF size mismatch: {actual_size} bytes, expected {SIZE}. {advice}"
            )
        actual_sha = digest(model_path)
    except OSError as exc:
        raise ModelPreparationError(f"Model GGUF unreadable: {model_path}. {advice}") from exc
    if actual_sha != SHA:
        raise ModelPreparationError(f"Model GGUF SHA256 mismatch: {model_path}. {advice}")
    return True
