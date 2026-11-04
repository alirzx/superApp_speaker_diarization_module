"""Protect the non-root Nginx runtime and team-owned host ports."""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
SERVICES = yaml.safe_load((ROOT / "docker-compose.yml").read_text())["services"]

def test_ui_uses_unprivileged_writable_mounts():
    ui = SERVICES["ui"]
    assert ui["read_only"] is True
    assert ui["cap_drop"] == ["ALL"]
    assert ui["ports"] == ['${UI_BIND_IP:-127.0.0.1}:${UI_PORT:-8084}:8080']
    assert ui["environment"]["APP_ENV"] == "${APP_ENV:-development}"
    for mount in ui["tmpfs"]:
        if mount.startswith(("/etc/nginx/conf.d:", "/var/cache/nginx:", "/var/run:", "/tmp:")):
            assert "uid=101,gid=101" in mount
    assert len(ui["tmpfs"]) == 4
    assert "8080/healthz" in str(ui["healthcheck"])

def test_nginx_does_not_need_root_or_chown_capabilities():
    dockerfile = (ROOT / "frontend/Dockerfile").read_text()
    nginx = (ROOT / "ops/nginx.conf.template").read_text()
    entrypoint = (ROOT / "ops/start-nginx.sh").read_text()
    assert "USER nginx" in dockerfile
    assert "ENTRYPOINT" in dockerfile
    assert "chown -R nginx:nginx" in dockerfile
    assert "pid /tmp/nginx.pid;" in nginx
    assert "listen 8080;" in nginx
    assert "location = /healthz" in nginx
    assert "proxy_pass http://$api_upstream;" in nginx
    assert "envsubst '${API_TOKEN}'" in entrypoint
    assert "exec nginx -c /tmp/nginx.conf" in entrypoint
