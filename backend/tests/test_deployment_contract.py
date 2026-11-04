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
