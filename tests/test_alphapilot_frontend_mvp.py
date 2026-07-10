from pathlib import Path

import pytest


@pytest.mark.unit
def test_frontend_workspace_contains_mvp_views_and_disclaimer():
    html = Path("frontend/index.html").read_text(encoding="utf-8")

    for marker in (
        "data-view=\"auth\"",
        "data-view=\"dashboard\"",
        "data-view=\"analysis\"",
        "data-view=\"compare\"",
    ):
        assert marker in html

    forbidden = (
        "data-target=\"new-analysis\"",
        "data-target=\"analysis-detail\"",
        "data-target=\"watchlist\"",
        "data-target=\"admin-users\"",
        "data-target=\"public-demo\"",
        "OpenBB-inspired analyst workspace",
        "<small>Research terminal</small>",
        "Route workflow",
        ">Watchlist<",
        ">Single<",
        "Run analysis",
        "Decision</span>\n                  <strong id=\"decisionMetric\">Overweight</strong>",
    )
    for marker in forbidden:
        assert marker not in html

    assert "Agentic stock research terminal" in html
    assert "How to use AlphaPilot" in html
    assert "Admin tools" in html
    assert "not financial advice" in html.lower()
    assert "AlphaPilot" in html
    assert "id=\"loginForm\"" in html
    assert "id=\"registerForm\"" in html
    assert "id=\"copilotForm\"" in html
    assert "id=\"copilotMessage\"" in html
    assert "id=\"copilotDraft\"" in html
    assert "id=\"accountButton\"" in html
    assert "id=\"localeToggle\"" in html
    assert "id=\"manageUsersAction\"" in html
    assert "id=\"accountLabel\"" in html
    assert "id=\"logoutAction\"" in html
    assert "Manage Users" in html
    assert "Logout" in html
    assert "id=\"analysisHistory\"" in html
    assert "id=\"analysisProgress\"" in html
    assert "id=\"analysisProgressStatus\"" in html
    assert "id=\"analysisStageBar\"" in html
    assert "id=\"analysisElapsed\"" in html
    assert "id=\"analysisUpdateAge\"" in html
    assert "id=\"compareProgress\"" in html
    assert "id=\"compareStageBar\"" in html
    assert "id=\"compareReport\"" in html
    assert "id=\"manualAnalysisPanel\"" in html
    assert "id=\"manualComparePanel\"" in html
    assert "id=\"reportLanguageToggle\"" in html
    assert "id=\"reportRendered\"" in html
    assert "<pre id=\"marketReport\"" not in html
    assert "<pre id=\"finalReport\"" not in html
    assert "<summary>Manual analysis</summary>" in html
    assert "<summary>Manual compare</summary>" in html
    assert "<details id=\"manualAnalysisPanel\" class=\"manual-workflow\">" in html
    assert "<details id=\"manualComparePanel\" class=\"manual-workflow\">" in html
    assert "<details id=\"manualAnalysisPanel\" class=\"manual-workflow\" open>" not in html
    assert "<details id=\"manualComparePanel\" class=\"manual-workflow\" open>" not in html


@pytest.mark.unit
def test_frontend_style_uses_dense_financial_dashboard_primitives():
    css = Path("frontend/styles.css").read_text(encoding="utf-8")

    assert ".workspace-shell" in css
    assert ".metric-strip" in css
    assert ".terminal-panel" in css
    assert ".report-grid" in css
    assert ".dashboard-workspace" in css
    assert ".copilot-panel" in css
    assert ".symbol-pill" in css
    assert ".account-area" in css
    assert ".progress-feed" in css
    assert ".progress-live-header" in css
    assert ".stage-track" in css
    assert ".stage-step" in css
    assert ".report-rendered" in css
    assert ".account-label" in css
    assert ".guide-panel" in css
    assert ".admin-users-panel" in css
    assert ".typewriter" in css
    assert ".manual-workflow" in css
    assert "--accent-positive" in css
    assert "--accent-warning" in css


@pytest.mark.unit
def test_frontend_javascript_connects_to_backend_api():
    js = Path("frontend/app.js").read_text(encoding="utf-8")

    assert "const API_BASE" in js
    assert "window.location.origin" in js
    assert "localStorage.setItem(\"alphapilot_token\"" in js
    assert "fetch(`${API_BASE}/auth/login`" in js
    assert "fetch(`${API_BASE}/auth/register`" in js
    assert "apiFetch(\"/analysis\"" in js
    assert "apiFetch(`/analysis/${jobId}`" in js
    assert "apiFetch(`/analysis/${jobId}/progress`" in js
    assert "apiFetch(\"/copilot/route\"" in js
    assert "apiFetch(\"/compare\"" in js
    assert "loadCurrentUser" in js
    assert "pollAnalysisJob" in js
    assert "renderProgressEvents" in js
    assert "renderProgressChrome" in js
    assert "ANALYSIS_STAGES" in js
    assert "COMPARE_STAGES" in js
    assert "renderMarkdown" in js
    assert "escapeHtml" in js
    assert "localized_sections?.zh?.report" in js
    assert "localized_sections?.zh?.final" in js
    assert "renderAdminUsers" in js
    assert "loadAdminUsers" in js
    assert "removeDraftSymbol" in js
    assert "selectDraftCandidate" in js
    assert "validateDraftBeforeConfirm" in js
    assert "renderCandidateGroups" in js
    assert "renderUnresolvedEntities" in js
    assert "data-remove-symbol" in js
    assert "data-candidate-query" in js
    assert "Compare workflows need 2 to 5 selected stocks." in js
    assert "Analysis workflows need at least one selected stock." in js
    assert "setLocale" in js
    assert "alphapilot_ui_locale" in js
    assert "renderDashboardGuide" in js
    assert "Admin access" in js
    assert "Manage Users" in js
    assert "Logout" in js
    assert "fetch(`${API_BASE}/demo/reference`" in js
    assert "deleteAnalysisJob" in js
    assert "deleteCompareWorkflow" in js
    assert "apiFetch(`/analysis/${jobId}`" in js
    assert "apiFetch(`/compare/${workflowId}`" in js
