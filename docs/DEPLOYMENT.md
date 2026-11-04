# Speaker Diarization: local and GitLab deployment

## Verified build result and recent failure

The GitLab log for commit 1e1c895 shows **both API and UI Docker images built**.
The failure happened when Docker marked the API unhealthy. The old Compose
had `model-setup` behind a profile and the DevOps job runs only
`git pull origin main && docker compose up --build -d`. Consequently a
fresh /models volume was not provisioned. API startup validates the model and
manifest; missing files prevent startup.

The Compose file now makes `model-setup` an unprofiled one-shot prerequisite
for API: **model-setup succeeds -> API becomes healthy -> UI starts**.
It installs the official pinned GGUF into persistent `model_cache` and
verifies SHA256 before publishing manifest. On subsequent deployments,
an intact cached model avoids downloading again. An unavailable Hugging Face
endpoint produces an explicit failed setup step instead of a mysterious
API health failure. This is the expected behavior; no bypass is allowed.

## Ports and network binding

| Service | Docker internal | Local .env | Server .env |
|---|---|---|---|
| API | api:8000 | 127.0.0.1:8003 | 127.0.0.1:8003 |
| UI | ui:8080 | 127.0.0.1:8084 | 192.168.4.209:8084 |

The server MUST own address 192.168.4.209. UI URLs for clients on the approved
LAN: http://192.168.4.209:8084. Permit inbound TCP 8084 from approved
networks only. Nginx proxies same-origin /api requests to api:8000.
Do NOT expose the API port to the public internet. Nginx injects a shared
API token; this is not per-user authorization. Add access controls (SSO,
authenticating gateway, restricted VPN) and HTTPS for production exposure.

## Local startup

```bash
cp .env.example .env   # preserve existing .env and API_TOKEN if already configured
chmod 600 .env
docker compose --env-file .env config --quiet
docker compose --env-file .env up --build -d
docker compose --env-file .env ps -a
docker compose --env-file .env logs --tail=100 model-setup api ui
curl -f http://127.0.0.1:8003/health/ready
```

Optionally prewarm/download the model:
`docker compose --env-file .env run --build --rm model-setup`.
This is not required for CI because Compose enforces the prerequisite itself.

## CI deployment (DevOps-owned, not modified by this change)

The actual executable pipeline is `.gitlab-ci.yml` and runs on branch
`main`. It copies GitLab File variable `ENV_FILE` to the deployment host,
then runs `git pull origin main && docker compose up --build -d`. Its
shell runner also requires `SSH_PRIVATE_KEY`, `SSH_USER`, `SSH_PORT`
and `VM_IPADDRESS`. The unrelated `.gitlab-ci-prod.yml` is NOT imported
by the current pipeline and must not be assumed active. Coordinate any CI
template changes with DevOps.

Production `ENV_FILE` must include all variables in
`.env.production.example`, particularly APP_ENV=production,
a strong unique API_TOKEN, API_PORT=8003, UI_BIND_IP=192.168.4.209,
and UI_PORT=8084. Do not place private keys or tokens in Git.

## Server diagnosis commands

```bash
cd /opt/apps/ai-service/speaker_diarization_module
docker compose --env-file .env config --quiet
docker compose --env-file .env ps -a
docker compose --env-file .env logs --no-color --tail=200 model-setup api ui
docker inspect superapp-speaker-diarization-api-1 --format '{{json .State.Health}}'
# Re-run provisioning manually if setup reports network or SHA issues:
docker compose --env-file .env run --rm model-setup
# Verify model exists without printing secrets:
docker compose --env-file .env run --rm --no-deps api python -c "from app.config import Settings;from app.services.model_manager import verify;s=Settings();verify(s.model_path,s.manifest_path);print('Model SHA256 OK')"
curl -f http://127.0.0.1:8003/health/ready
```

A missing model, checksum mismatch, insufficient disk, access to Hugging Face,
bad CPU runtime or a production token below 32 characters can all stop API
startup. **The log provided did not include API application logs**, so the
exact historical exception is not confirmed.

Never run `docker compose down -v` during ordinary deployments: it
would erase the persistent model cache. Monitor `model-setup` exit code,
API health status, UI health and endpoint response separately. Model
quality and RTF for Persian/English have NOT been benchmarked yet.
