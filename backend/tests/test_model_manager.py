"""Model-cache contract, including the original missing-manifest server failure."""
import hashlib
import json

import pytest

from app.services import model_manager as models


@pytest.fixture
def fixture_model(tmp_path, monkeypatch):
    payload = b"verified-test-GGUF"
    monkeypatch.setattr(models, "SIZE", len(payload))
    monkeypatch.setattr(models, "SHA", hashlib.sha256(payload).hexdigest())
    model = tmp_path / models.NAME
    manifest = tmp_path / "manifest.json"
    model.write_bytes(payload)
    manifest.write_text(json.dumps({
        "repo": models.REPO, "revision": models.REV,
        "sha256": models.SHA, "filename": models.NAME
    }))
    return model, manifest


def test_verified_cached_model(fixture_model):
    model, manifest = fixture_model
    assert models.verify(model, manifest) is True


def test_missing_manifest_gives_actionable_diagnostics(fixture_model):
    model, manifest = fixture_model
    manifest.unlink()
    with pytest.raises(models.ModelPreparationError, match="model-setup"):
        models.verify(model, manifest)


def test_invalid_manifest_rejected(fixture_model):
    model, manifest = fixture_model
    manifest.write_text("not json")
    with pytest.raises(models.ModelPreparationError, match="unreadable/invalid"):
        models.verify(model, manifest)


def test_invalid_revision_rejected(fixture_model):
    model, manifest = fixture_model
    metadata = json.loads(manifest.read_text())
    metadata["revision"] = "latest"
    manifest.write_text(json.dumps(metadata))
    with pytest.raises(models.ModelPreparationError, match="identity mismatch"):
        models.verify(model, manifest)


def test_missing_gguf_rejected(fixture_model):
    model, manifest = fixture_model
    model.unlink()
    with pytest.raises(models.ModelPreparationError, match="GGUF missing"):
        models.verify(model, manifest)


def test_corrupted_gguf_rejected(fixture_model):
    model, manifest = fixture_model
    model.write_bytes(b"bad")
    with pytest.raises(models.ModelPreparationError, match="size mismatch"):
        models.verify(model, manifest)


def test_same_size_wrong_gguf_rejected(fixture_model):
    model, manifest = fixture_model
    model.write_bytes(b"x" * model.stat().st_size)
    with pytest.raises(models.ModelPreparationError, match="SHA256 mismatch"):
        models.verify(model, manifest)
