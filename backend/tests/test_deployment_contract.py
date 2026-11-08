"""Regression checks for the DevOps up --build -d workflow."""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = yaml.safe_load((ROOT / "docker-compose.yml").read_text())

def test_setup_runs_before_api_even_without_profile():
    services = COMPOSE["services"]
    assert "profiles" not in services["model-setup"]
    assert services["api"]["depends_on"]["model-setup"]["condition"] == "service_completed_successfully"
    assert services["ui"]["depends_on"]["api"]["condition"] == "service_healthy"
    assert services["api"]["volumes"] == ["model_cache:/models:ro"]
    assert services["model-setup"]["volumes"] == ["model_cache:/models"]

def test_ports_and_healthchecks_remain_compatible_with_team():
    services = COMPOSE["services"]
    assert any("8003" in value and value.endswith(":8000") for value in services["api"]["ports"])
    assert any("8084" in value and value.endswith(":8080") for value in services["ui"]["ports"])
    assert "healthcheck" in services["api"]
    assert "healthcheck" in services["ui"]
    assert "MODEL_PATH" in services["api"]["environment"]
    assert "MODEL_MANIFEST" in services["api"]["environment"]


def test_pip_mirror_build_args_all_python_images():
    services = COMPOSE["services"]
    for service in ("api", "model-setup"):
        args = services[service]["build"]["args"]
        assert "package-mirror.liara.ir/repository/pypi/simple" in args["PIP_PRIMARY_INDEX_URL"]
        assert "mirror2.chabokan.net/pypi/simple" in args["PIP_FALLBACK_INDEX_URL"]
    # The UI uses npm + Nginx, not Python requirements.
    for filename in ("backend/Dockerfile", "backend/Dockerfile.setup"):
        dockerfile = (ROOT / filename).read_text()
        assert "PIP_PRIMARY_INDEX_URL" in dockerfile
        assert "PIP_FALLBACK_INDEX_URL" in dockerfile
        assert '--index-url "$PIP_PRIMARY_INDEX_URL"' in dockerfile
        assert '--index-url "$PIP_FALLBACK_INDEX_URL"' in dockerfile
        assert "pypi.org" not in dockerfile
        assert "--extra-index-url" not in dockerfile

def test_ui_bind_not_forced_to_loopback():
    ui = COMPOSE["services"]["ui"]
    assert ui["ports"] == ["${UI_BIND_IP:-127.0.0.1}:${UI_PORT:-8084}:8080"]
    prod = (ROOT / ".env.production.example").read_text()
    assert "UI_BIND_IP=192.168.4.209" in prod
