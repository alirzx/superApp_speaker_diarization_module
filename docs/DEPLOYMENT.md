# Speaker Diarization deployment and failure diagnosis

## Original server failure

The old GitLab deploy log built both images, then Docker reported API unhealthy.
The additional API traceback confirmed `FileNotFoundError: /models/manifest.json`.
The deployed revision did not require setup because `model-setup` was a
separate Compose profile. As a result, an empty model volume was mounted
read-only by the API.

The fixed main branch uses an unprofiled, one-shot `model-setup` with
`depends_on: service_completed_successfully`. It downloads/validates the
GGUF, publishes manifest last, and then permits API/health and UI startup.
Artifact file permissions are set so UID 10001 in API can read them.

## Host network

- Local API: `127.0.0.1:8003`.
- Local UI: `127.0.0.1:8084`.
- Server API: `127.0.0.1:8003` (keep private).
- Server UI: `192.168.4.209:8084` (approved LAN clients).

Only use 192.168.4.209 if the deployment server owns that address. Secure LAN
access with firewall and trusted authenticated gateway; Nginx's shared token
is *not* user authentication.

## CI and deploy

The team-owned active `.gitlab-ci.yml` is unchanged. It copies GitLab's
File-type `ENV_FILE` and executes
`git pull origin main && docker compose up --build -d`.
Variables: `ENV_FILE`, `SSH_PRIVATE_KEY`, `SSH_USER`, `SSH_PORT`,
`VM_IPADDRESS`. The unused `.gitlab-ci-prod.yml` is separate and is not
included by the current runner.

The deployment machine must reach Hugging Face on first setup, or the
persistent model volume must already contain a verified pinned GGUF.
Model cache is not stored in Git and must not be cleared during normal deploy.
Use the provided `.env.production.example` (strong private API_TOKEN required)
and configure `UI_BIND_IP=192.168.4.209`.

## Before retry

```bash
cd /opt/apps/ai-service/speaker_diarization_module
docker compose --env-file .env config --quiet
docker compose --env-file .env ps -a
docker compose --env-file .env logs --tail=150 model-setup api ui
```

After the update is pushed to GitLab and the runner deploys:

```bash
docker compose --env-file .env ps -a
docker compose --env-file .env logs --no-color --tail=200 model-setup api ui
curl -fsS http://127.0.0.1:8003/health/ready
curl -fsSI http://192.168.4.209:8084/
```

For an offline isolated test, the setup container can be run without touching
running API/UI services:

```bash
docker compose --env-file .env run --rm model-setup
docker compose --env-file .env run --rm --no-deps api \
  python -c "from app.config import Settings;from app.services.model_manager import verify;s=Settings();assert verify(s.model_path,s.manifest_path);print('Model verified')"
```

A missing or corrupted model now causes an explicit `ModelPreparationError`
with the path and setup-log hint instead of an unhandled FileNotFoundError.
If setup fails, inspect network/DNS/TLS access to Hugging Face, available disk
space and storage permissions. If startup fails after setup, inspect API logs,
model-manifest identity and the native executable. Do not disable SHA256 checks.

**Do not use `docker compose down -v`** because it would erase the model
cache. CPU throughput, DER on Persian/English and production release testing
remain unverified.

## UI Nginx permission repair (non-root)

The API may be healthy while the UI restarts with `Operation not permitted`
because the official Nginx image's root entrypoint attempts cache setup or
privilege transitions when Compose has `cap_drop: [ALL]` and a read-only FS.
We follow the Persian sentiment module's proven non-root design instead of
re-enabling CHOWN/SETUID/SETGID or running Nginx as root.

- The frontend image installs `gettext`, prepares writable directories at
  build time, and runs with `USER nginx` (Alpine UID/GID 101).
- Compose mounts `/etc/nginx/conf.d`, `/var/cache/nginx`, `/var/run`,
  and `/tmp` as tmpfs with `uid=101,gid=101`. These options matter:
  a tmpfs mount hides image-layer chown ownership.
- Custom `ops/start-nginx.sh` validates the production token, renders only
  `API_TOKEN` into `/tmp/nginx.conf` with restrictive umask, checks Nginx
  syntax and execs Nginx.
- The full Nginx configuration sets `pid /tmp/nginx.pid`, listens on 8080,
  and provides `GET /healthz` for Docker's UI healthcheck. Docker's DNS is
  used for API proxying; uploads are not buffered to the limited cache tmpfs.
- CI, API, model cache, ports (8003/8084) and server `UI_BIND_IP`
  (192.168.4.209) remain unchanged.

After GitLab deploys the updated commit, on the server:

```bash
cd /opt/apps/ai-service/speaker_diarization_module
docker compose --env-file .env config --quiet
docker compose --env-file .env ps -a
docker compose --env-file .env logs --tail=120 ui
docker compose --env-file .env exec -T ui nginx -t -c /tmp/nginx.conf
docker compose --env-file .env port ui 8080
curl --noproxy '*' -fsS http://192.168.4.209:8084/healthz
curl --noproxy '*' -fsSI http://192.168.4.209:8084/
curl --noproxy '*' -fsS http://192.168.4.209:8084/api/health/ready
```

If Nginx is now healthy but another workstation cannot reach the UI, next
check the `ENV_FILE` in GitLab, published host address, firewall, and VPN
routing. No new API token is needed if the existing production token is valid.

## Python package install mirrors (build stage only)

The CPU builder needs `cmake==3.30.9`, the API image installs
`backend/requirements.txt`, and the one-shot model-setup image installs
`huggingface-hub==0.34.4`. All three pip install sites now attempt the
Liara mirror first and retry using Chabokan only if Liara fails:

- `PIP_PRIMARY_INDEX_URL=https://package-mirror.liara.ir/repository/pypi/simple`
- `PIP_FALLBACK_INDEX_URL=https://mirror2.chabokan.net/pypi/simple/`

Values are passed from the host `.env` into both Python image Docker builds
as build args. Each pip call explicitly sets `--index-url`, so it does not
implicitly query the default PyPI index. We intentionally avoid
`--extra-index-url`: it is not prioritized failover. pip operations use
15-second connection timeout, 2 retries and independent BuildKit caches for
successful wheel downloads. Both mirrors must have the pinned packages or
an approved internal mirror must be supplied as a build argument.

**This is not a runtime inference timeout fix.** Package indexes are used
when Docker builds new Python images. The GGUF model is downloaded from
Hugging Face by `model-setup` (unless verified in the persistent /models
volume); package mirrors do not mirror the GGUF. npm, Debian apt and the
pinned GitHub NeMo native source use separate providers.

A running UI returning HTTP 503 usually means the API inference queue
was unavailable/occupied (default 1 concurrent, 10-second queue timeout),
while a browser `NetworkError` might be an interrupted proxy connection,
container OOM/restart, client VPN, or other network failure. Inspect
the request Status, response payload, API logs and memory before changing
inference timeout or worker count. Do not treat build mirrors as a fix for
an audio processing outage.

## LAN / VPN UI check

Server `ENV_FILE` (GitLab **File** variable) must retain
`UI_BIND_IP=192.168.4.209`, `UI_PORT=8084`.
The existing Compose maps that host address to Nginx's container port 8080
and keeps the API on `127.0.0.1:8003`. Verify, without displaying tokens:

```bash
cd /opt/apps/ai-service/speaker_diarization_module
grep -E '^(API_BIND_IP|API_PORT|UI_BIND_IP|UI_PORT)=' .env
docker compose port ui 8080
docker compose ps -a
curl --noproxy '*' -fsS http://192.168.4.209:8084/healthz
curl --noproxy '*' -fsS http://192.168.4.209:8084/api/health/ready
```

If local server curl works but a LAN/VPN laptop fails, examine the approved
firewall ACL, routing and VPN split-tunnel policies. The source code cannot
ensure inter-network reachability. Do not bind the API publicly as a
workaround. No changes to DevOps-owned CI templates are needed.
