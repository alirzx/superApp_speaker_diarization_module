# SuperApp Speaker Diarization

CPU-first, stand-alone diarization for Persian and English audio using
**NVIDIA Nemotron 3 Diarization** (Q8 GGUF) with native **NeMo-Speech.cpp**.
Identifies *speaker turns*, not the real identity of any speaker.

**Current status:** the server built both API and UI images, but an earlier
deployment stopped at API health check. This update makes the first-use model
download mandatory before API startup. A successful rebuilt deployment and
real-audio inference are **not yet confirmed**.

## Components

- FastAPI: bounded audio upload and ffmpeg 16-kHz mono PCM conversion.
- Native CPU diarization: anonymous speaker slots and overlap-preserving
  JSON / RTTM output.
- React and Nginx: Persian RTL UI with audio player, speaker timeline
  and downloadable results.
- Dedicated model setup: immutable Hugging Face revision, SHA256 verification,
  persistent named Docker model cache, idempotent one-shot service.
- Resource and security controls: non-root read-only API, concurrency
  semaphore, API token, size/duration caps and health checks.

## Startup

```bash
# Existing .env users: KEEP your secret API_TOKEN.
# Only change port/bind variables if they differ from team configuration.
docker compose --env-file .env config --quiet
docker compose --env-file .env up --build -d
docker compose --env-file .env ps -a
docker compose --env-file .env logs --tail=150 model-setup api ui
```

`docker compose up --build -d` now starts `model-setup` first and waits for it
to complete successfully. On a new server, this requires internet access to
Hugging Face or a trusted pre-populated model volume. Subsequent deployments
reuse the cached model if SHA256 matches. **Do not use `down -v`**.

## Network

| Component | Local | GitLab deployment server |
|---|---|---|
| API | http://127.0.0.1:8003 | http://127.0.0.1:8003 |
| UI | http://127.0.0.1:8084 | http://192.168.4.209:8084 |

The server UI is LAN-bound, while the API stays loopback-only.
Nginx forwards /api to the API service over the Docker network. Allow
inbound TCP 8084 from approved clients and use authenticated ingress/TLS.

## API

| Method | Path | Description |
|---|---|---|
| GET | /health/live | Process liveness |
| GET | /health/ready | Startup readiness |
| GET | /v1/models | Model metadata; X-API-Key |
| POST | /v1/diarize | Audio -> JSON or RTTM; X-API-Key |
| GET | /metrics | Prometheus; X-API-Key |

```bash
curl -f http://127.0.0.1:8003/health/ready
curl -f -H "X-API-Key: $API_TOKEN" -F 'file=@meeting.wav' \
  http://127.0.0.1:8003/v1/diarize
```

## GitLab CI and release gates

The team-owned `.gitlab-ci.yml` remains unchanged. It deploys via SSH
to `/opt/apps/ai-service/speaker_diarization_module` and executes
`git pull origin main && docker compose up --build -d`. Compose now handles
model provisioning through `depends_on: service_completed_successfully`.
The older `.gitlab-ci-prod.yml` is not part of the active pipeline.

To inspect a failed rollout:
`docker compose ps -a` and
`docker compose logs --tail=150 model-setup api ui`.

**Remaining release validation:** model download on the GitLab VM,
CPU inference with real Persian and English audio, speaker metrics (DER/RTF),
resource limits, CI runtime and authenticated LAN exposure.

See [Deployment](docs/DEPLOYMENT.md), [Architecture](docs/ARCHITECTURE.md),
[API](docs/API.md), [Security](docs/SECURITY.md), [Model provenance](docs/MODEL_PROVENANCE.md),
and [Test plan](docs/TEST_PLAN.md).
