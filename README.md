# SuperApp Speaker Diarization

CPU-first, stand-alone diarization for Persian and English audio using
**NVIDIA Nemotron 3 Diarization** (Q8 GGUF) with native **NeMo-Speech.cpp**.
Identifies *speaker turns*, not the real identity of any speaker.

**Current status:** the deployment now builds API/UI and reports API healthy,
but the server UI was restarting with an Nginx permission error. This revision
matches the working non-root Nginx layout from the Persian sentiment module:
UID 101 owns writable tmpfs mounts, /tmp holds the generated configuration
and PID, and no elevated Linux capabilities are granted. The repaired image
still needs a fresh deployment and HTTP health verification. Real-audio CPU
inference remains unbenchmarked.

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

## UI permission fix and healthcheck

UI runs as the Alpine `nginx` user (UID/GID 101), with a read-only image
and writable UID-101 tmpfs mounts for Nginx cache, PID and generated config.
The entrypoint safely renders only `API_TOKEN` to `/tmp/nginx.conf`, tests
syntax, and starts Nginx without root privileges. Health endpoint:
`GET /healthz` on UI port 8080 (host 8084). Verify after deployment:

```bash
docker compose ps -a
docker compose logs --tail=100 ui
curl -f http://192.168.4.209:8084/healthz
```

## Regional Python package mirrors

Docker builds of the native CMake builder, FastAPI backend and model-setup
use Liara as primary and Chabokan as the sequential fallback for Python
package installation, with explicit `--index-url` and bounded retries.
The build args `PIP_PRIMARY_INDEX_URL` / `PIP_FALLBACK_INDEX_URL` are
set in `docker-compose.yml` and can be overridden in local/server `.env`.
The audio model still downloads via Hugging Face, with persistent GGUF
cache: pip mirrors do not speed up CPU inference or fix UI request timeouts.

The server UI binds to `UI_BIND_IP=192.168.4.209`, `UI_PORT=8084`
through the host's production `.env`; API remains loopback-only. Ensure
the actual GitLab File variable `ENV_FILE` contains these values.

## Debian APT mirror failover

Build-stage `apt-get` now uses a shared helper in
`ops/install-debian-packages.sh`, replacing the unavailable
`deb.debian.org:80` sources with signed Debian Bookworm repositories over
HTTPS. It attempts a primary mirror, then a fallback, and fails explicitly
if neither can be reached. Both mirrors are configurable using
`APT_PRIMARY_DEBIAN_URL`, `APT_PRIMARY_SECURITY_URL`,
`APT_FALLBACK_DEBIAN_URL`, and `APT_FALLBACK_SECURITY_URL`
(Docker build args in Compose). PyPI still uses Liara/Chabokan independently.
No change to GitLab CI, API/UI ports, Nginx bind, or model cache.
