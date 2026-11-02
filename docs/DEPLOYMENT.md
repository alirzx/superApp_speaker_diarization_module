# Local and server deployment

## Service layout

Host API port **8003** -> container port 8000. Host UI port **8084** -> container port 8080.
Both host binds default to 127.0.0.1; never change teammates' ports without agreement.
Frontend Nginx proxies /api/* to the internal api:8000 container.
The CPU inference uses NVIDIA NeMo-Speech.cpp with pinned GGUF weights.
The standalone CLI is loaded for each request, so benchmark cold/warm latency before claiming real-time support.

## Initial development setup

```bash
cp .env.example .env
chmod 600 .env
# Generate an environment-specific API_TOKEN for real access-control tests:
# openssl rand -hex 32
docker compose --env-file .env config --quiet
make model
make build
make up
curl -f http://127.0.0.1:8003/health/ready
```

UI: http://127.0.0.1:8084. Use curl with X-API-Key for direct authenticated API calls.
Do not commit .env or recordings. Model files live in the Docker named volume, not the repo.

## Production variables and CI/CD

Production requires APP_ENV=production, a unique random API_TOKEN (>=32 chars),
and the same token inside the API and UI Nginx containers (Compose passes it to both).
Copy .env.production.example to a private deploy file and replace its placeholder;
never put the real token in Git.
Default CPU_THREADS=2, MAX_CONCURRENT_INFERENCE=1, API_CPUS=2.0,
API_MEMORY=1500m, UI_CPUS=0.5 and UI_MEMORY=256m are **unverified starting limits**.
Tune after real CPU tests.

`.gitlab-ci.yml` includes `.gitlab-ci-prod.yml`; deploy-production is intentionally
**manual on main** and uses deployment runner tags linux/bina/shell.
Protected CI/CD variables required:

- SSH_PRIVATE_KEY_FILE: GitLab **File** variable with a deployment-only private SSH key.
- SSH_KNOWN_HOSTS: GitLab **File** variable with preverified SSH host keys.
- ENV_FILE: GitLab **File** variable whose contents are the complete production .env.
- SSH_USER, SSH_PORT, VM_IPADDRESS: protected text variables.

The deploy target is `/opt/apps/ai-service/speaker_diarization_module`.
Pre-provision that directory as a clone of the organization's GitLab repository,
with origin pointing to GitLab, and allow the deployment user to use Docker.
A protected main branch is required to expose protected variables.
The job updates main with `git merge --ff-only origin/main`, installs the
.env securely, prepares the pinned model, builds both images, and starts api/ui.
The runner requires ssh/scp and Docker on the target; the server requires
GitLab/Hub access or approved mirrors at build/setup time. This CI job
does **not** silently initialize a new repository.

Before enabling server deployment, validate the native binary on CPU, benchmark
Persian and English recordings, check DER, p95 latency, RSS, and model licensing.
The current production job is a manual bootstrap/deployment recipe, not
evidence that model inference was tested or a release passed acceptance gates.

## Validation

```bash
PYTHONPATH=backend pytest -q backend/tests
docker compose --env-file .env config --quiet
docker compose --env-file .env --profile setup run --rm model-setup
docker compose --env-file .env build api ui
docker compose --env-file .env up -d api ui
docker compose --env-file .env ps
curl -f http://127.0.0.1:8003/health/ready
```

Do not disable SHA256 verification to work around a network failure.
If build access is blocked, mirror dependencies and model artifacts via a
trusted internal registry or cache and retain immutable pins.
