# SuperApp Speaker Diarization

**CPU-first speaker diarization for Persian and English recordings**, powered by NVIDIA **Nemotron 3 Diarization** (GGUF Q8) and the native **NeMo-Speech.cpp** runtime. Detects *who spoke when* using anonymous recording-local speaker labels. It does **not** establish identity or transcribe words.

**Status:** implementation / pre-production validation. CPU model inference on a real recording, Docker build, CI deployment, and Persian/English quality are **not yet verified**.

## Features

- WAV, MP3, FLAC, M4A, OGG and OPUS upload; ffmpeg decoding to 16 kHz mono PCM16.
- Speaker timeline, audio playback, JSON and RTTM exports in Persian RTL React UI.
- FastAPI validation, bounded uploads and inference concurrency, readiness, metrics, X-API-Key.
- Native CPU-only model with pinned source and model versions, SHA256 verified at startup.
- Separate setup image, Docker Compose, GitLab CI test/build and manual production deployment.

## Quick start

Docker with Compose, an internet-connected one-time model setup, and native compilation dependencies are required.

```bash
cp .env.example .env
chmod 600 .env
# Optional for local dev, REQUIRED for production: set a unique API_TOKEN
# openssl rand -hex 32
make model
make build
make up
curl -f http://127.0.0.1:8003/health/ready
```

| Component | Host | Container |
| --- | --- | --- |
| REST API | http://127.0.0.1:8003 | api:8000 |
| React UI | http://127.0.0.1:8084 | ui:8080 |

Both host ports **8003** and **8084** were selected by the deployment team and are preserved.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | /health/live | Liveness |
| GET | /health/ready | Readiness (model verified at startup) |
| GET | /v1/models | Model metadata (X-API-Key) |
| POST | /v1/diarize | Multipart audio, JSON or RTTM |
| GET | /metrics | Prometheus (X-API-Key) |

```bash
curl -f -H "X-API-Key: $API_TOKEN" \
  -F "file=@meeting.wav" http://127.0.0.1:8003/v1/diarize
```

**Audio data flow:** Browser -> Nginx /api -> FastAPI -> ffmpeg -> WAV 16k mono -> Nemotron 3 CPU via native CLI -> normalized segments -> JSON/RTTM/UI.

Speaker labels are recording-local (SPEAKER_00 etc.). The API supports overlapping speech segments, not speaker identity matching. Each request starts a new native CLI process; actual latency depends on CPU and duration.

## Model provenance

| Field | Value |
| --- | --- |
| Model | nvidia/Nemotron-3-Diarization |
| Revision | `f667ed73aee57d40cc39428eb768b4fd87a0a29e` |
| GGUF | `Nemotron-3-Diarization.q8_0.gguf` |
| Size | 107012128 bytes |
| SHA256 | `08456d9e22cd9a323c0364d98375f3746d6e68507ebb705cd46438c534c7a3a1` |
| Native source | NVIDIA/NeMo-Speech.cpp @ `20999cc921d2b14aa58708f61756a8b2e787ba20` |
| Model license | NVIDIA Open Model License (OpenMDW 1.1) |

Model files are downloaded by `make model`, not committed to Git. Review commercial and redistributable usage terms.

## Test and deployment

```bash
pip install -r backend/requirements-dev.txt
PYTHONPATH=backend pytest -q backend/tests
docker compose --env-file .env config --quiet
```

GitLab CI runs Python unit tests and the React build. The deployment job is **manual on main**, with protected SSH/ENV File variables. It targets `/opt/apps/ai-service/speaker_diarization_module` and requires a pre-provisioned checkout and Docker privileges.

See [Architecture](docs/ARCHITECTURE.md), [API](docs/API.md), [Deployment](docs/DEPLOYMENT.md), [Model provenance](docs/MODEL_PROVENANCE.md), [Security](docs/SECURITY.md), and [Test plan](docs/TEST_PLAN.md).

**Release gates:** actual CPU model load/inference, source build and dynamic-link checks, audio fixtures, DER and RTF on Persian/English with overlaps, p95/RSS benchmark, authenticated ingress, CI runner and deployment credential validation.
