# SuperApp Speaker Diarization

CPU-first standalone speaker diarization for Persian and English audio using NVIDIA Nemotron 3 Diarization and the native NeMo-Speech.cpp CLI.

## Development status

The implementation source bundle has been assembled and mock-based Python tests passed, but **the complete source bundle has not yet been pushed to this GitHub repository**. Native model download, CPU build, real-audio inference, frontend build and production deployment have not been verified. Do not treat this repository as production-ready.

## Planned integration

- FastAPI POST /v1/diarize, GET /health/live, GET /health/ready, GET /v1/models and GET /metrics.
- React + TypeScript frontend with speaker timeline and JSON/RTTM export.
- CPU-only native CLI, pinned NVIDIA model revision and SHA256, dedicated model setup container.
- Docker Compose, GitLab CI, tests, resource limits, bounded uploads and private serving.

Model: nvidia/Nemotron-3-Diarization; revision f667ed73aee57d40cc39428eb768b4fd87a0a29e; GGUF SHA256 08456d9e22cd9a323c0364d98375f3746d6e68507ebb705cd46438c534c7a3a1.
