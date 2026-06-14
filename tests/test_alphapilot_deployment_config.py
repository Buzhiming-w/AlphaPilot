from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase6_deployment_files_describe_single_server_stack():
    compose = (ROOT / "docker-compose.prod.yml").read_text()
    caddyfile = (ROOT / "Caddyfile").read_text()

    for service in ("caddy:", "api:", "worker:", "postgres:", "redis:"):
        assert service in compose
    assert "uvicorn alphapilot.backend.app:app" in compose
    assert "python -m alphapilot.backend.worker" in compose
    assert "Caddyfile" in compose
    assert "reverse_proxy api:8000" in caddyfile
    assert "file_server" in caddyfile
    for api_prefix in ("/copilot/*", "/watchlist*", "/compare*"):
        assert f"handle {api_prefix}" in caddyfile


def test_production_env_example_has_required_keys_without_real_secrets():
    env_example = (ROOT / ".env.production.example").read_text()

    required_keys = [
        "ALPHAPILOT_DATABASE_URL=",
        "ALPHAPILOT_REDIS_URL=",
        "ALPHAPILOT_QUEUE_BACKEND=redis",
        "ALPHAPILOT_RATE_LIMIT_ENABLED=true",
        "DEEPSEEK_API_KEY=",
        "TRADINGAGENTS_LLM_PROVIDER=deepseek",
    ]
    for key in required_keys:
        assert key in env_example
    assert "sk-" not in env_example
    assert "your-domain.example" in env_example
