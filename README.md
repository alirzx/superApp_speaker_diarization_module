# SuperApp Speaker Diarization

CPU-first, standalone **speaker diarization** for Persian and English recordings using NVIDIA **Nemotron 3 Diarization** with the **NeMo-Speech.cpp** native GGUF CPU runtime. It returns anonymous speaker labels and time-aligned segments. It **does not** identify real-world people or transcribe speech.

## Capabilities

- Upload WAV, MP3, FLAC, M4A, OGG and OPUS; normalize to mono 16-kHz PCM WAV with ffmpeg.
- NVIDIA Nemotron 3 Q8 model (up to 8 speaker slots), CPU-only execution, overlap-preserving JSON and RTTM.
- Persian RTL React/TypeScript interface with audio player and speaker timeline.
- FastAPI, private Nginx proxy, API key, bounded uploads, decoded-duration limits, concurrency semaphore, Prometheus and readiness.
- Separate model installer, pinned model and native source revisions, SHA256 verification, Docker Compose and GitLab CI.

## Quick start

Prerequisites: Docker + Compose and network access for the initial model download and native runtime build.

```bash
cp .env.example .env
make model
make build
make up
curl --fail http://127.0.0.1:8002/health/ready
```

UI: http://127.0.0.1:8083. API: http://127.0.0.1:8002. Configure a strong private API_TOKEN (32+ characters) and APP_ENV=production before production use; add user authentication and HTTPS at your ingress gateway.

```bash
curl -f -H "X-API-Key: $API_TOKEN" -F 'file=@meeting.wav' http://127.0.0.1:8002/v1/diarize
```

## Endpoints

| Route | Purpose |
|---|---|
| GET /health/live | Process liveness |
| GET /health/ready | Model readiness |
| GET /v1/models | Selected model information |
| POST /v1/diarize | Multipart audio; output_format json or rttm |
| GET /metrics | Prometheus metrics |

## Data flow

Browser -> Nginx /api -> FastAPI -> bounded upload -> ffmpeg decode -> mono PCM WAV -> **nemo-speech diarize --device cpu --preset v3-streaming** -> JSON validation -> normalized speaker segments -> JSON/RTTM/UI.

**Current performance caveat:** a new native CLI subprocess is started per request, including a potential model reload. Persistent native serving can be evaluated after real CPU profiling. pyannote and sherpa-onnx modules are placeholders and not operational backends.

## Model provenance

- Model: nvidia/Nemotron-3-Diarization
- Immutable revision: f667ed73aee57d40cc39428eb768b4fd87a0a29e
- Q8 file: Nemotron-3-Diarization.q8_0.gguf, 107,012,128 bytes
- SHA256: 08456d9e22cd9a323c0364d98375f3746d6e68507ebb705cd46438c534c7a3a1
- Native runtime: NVIDIA/NeMo-Speech.cpp @ 20999cc921d2b14aa58708f61756a8b2e787ba20
- Model license: NVIDIA Open Model License (OpenMDW 1.1). Review commercial use and distribution terms, plus dependencies.

## Validation status

**Pre-production implementation.** Mock API tests are not equivalent to real CPU inference. Verify Docker build/linking, actual Persian and English clips (including overlap), DER, RTF, peak RSS, p50/p95 latency, security and commercial license before rollout.

Run unit tests: `pip install -r backend/requirements-dev.txt && PYTHONPATH=backend pytest -q backend/tests`.

Documentation: [API](docs/API.md) · [Architecture](docs/ARCHITECTURE.md) · [Deployment](docs/DEPLOYMENT.md) · [Security](docs/SECURITY.md) · [Test plan](docs/TEST_PLAN.md).
