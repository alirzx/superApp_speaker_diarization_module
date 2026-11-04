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
