# Nemotron 3 model provenance and integrity

The official NVIDIA NeMo-Speech.cpp model index at the pinned runtime revision
lists this GGUF artifact:

- Hugging Face repository: `nvidia/Nemotron-3-Diarization`
- Exact revision: `f667ed73aee57d40cc39428eb768b4fd87a0a29e`
- File: `Nemotron-3-Diarization.q8_0.gguf`
- Size: `107012128` bytes
- SHA256: `08456d9e22cd9a323c0364d98375f3746d6e68507ebb705cd46438c534c7a3a1`
- License: NVIDIA Open Model License (OpenMDW 1.1). Review use/redistribution terms.

Native runtime is built from NVIDIA/NeMo-Speech.cpp commit
`20999cc921d2b14aa58708f61756a8b2e787ba20` (CPU-diar preset).
The CLI uses `--device cpu`. The build and runtime share Debian Bookworm.

## Lifecycle

1. `docker compose up --build -d` starts unprofiled `model-setup` first.
2. Setup validates cached GGUF size and SHA256, or downloads the pinned
   Hugging Face file into the persistent `model_cache` volume.
3. Model is installed by atomic rename; manifest is written last, and both
   are mode 0644 for the non-root API (UID 10001).
4. Setup verifies the final model + manifest before returning exit code 0.
5. Compose starts the API only after `service_completed_successfully`.
   API mounts /models read-only and performs the same verification on startup.
6. UI starts only after API health succeeds.

`HF_HOME=/models/.cache` keeps the Hub download cache on the SAME named
volume; no new downloads are required when GGUF is valid. Avoid `down -v`.
A failed download, missing manifest or bad hash fails closed. Inspect
`docker compose logs model-setup` and `docker compose logs api` for details.

The original server error at commit 1e1c895 was
`FileNotFoundError: /models/manifest.json`. The unprofiled model-setup
dependency was introduced in commit 4813d21. This revision additionally
provides explicit startup errors and readable artifact permissions.
The corrected deployment has not yet been confirmed by a new server run.
