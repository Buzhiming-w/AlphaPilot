from pathlib import Path

import pytest


@pytest.mark.unit
def test_frontend_workspace_contains_mvp_views_and_disclaimer():
    html = Path("frontend/index.html").read_text(encoding="utf-8")

    for marker in (
        "data-view=\"auth\"",
        "data-view=\"dashboard\"",
        "data-view=\"new-analysis\"",
        "data-view=\"analysis-detail\"",
        "data-view=\"admin-users\"",
        "data-view=\"public-demo\"",
    ):
        assert marker in html

    assert "not financial advice" in html.lower()
    assert "AlphaPilot" in html
    assert "id=\"loginForm\"" in html
    assert "id=\"registerForm\"" in html


@pytest.mark.unit
def test_frontend_style_uses_dense_financial_dashboard_primitives():
    css = Path("frontend/styles.css").read_text(encoding="utf-8")

    assert ".workspace-shell" in css
    assert ".metric-strip" in css
    assert ".terminal-panel" in css
    assert ".report-grid" in css
    assert "--accent-positive" in css
    assert "--accent-warning" in css


@pytest.mark.unit
def test_frontend_javascript_connects_to_backend_api():
    js = Path("frontend/app.js").read_text(encoding="utf-8")

    assert "const API_BASE" in js
    assert "localStorage.setItem(\"alphapilot_token\"" in js
    assert "fetch(`${API_BASE}/auth/login`" in js
    assert "fetch(`${API_BASE}/auth/register`" in js
    assert "apiFetch(\"/analysis\"" in js
    assert "apiFetch(`/analysis/${job.id}`" in js
    assert "fetch(`${API_BASE}/demo/reference`" in js
