const API_BASE = localStorage.getItem("alphapilot_api_base") || window.location.origin;

const demoResult = {
  decision: "Overweight",
  elapsed_seconds: 267,
  sections: {
    market: "Market analysis is available from the saved Phase 1 NVDA smoke run. Connect the API to load the full report in live mode.",
    final: "Final decision: Overweight. This sample is presented for product demonstration only and is not financial advice."
  }
};

let authToken = localStorage.getItem("alphapilot_token") || "";
let lastCopilotDraft = null;

const views = document.querySelectorAll(".view");
const navItems = document.querySelectorAll(".nav-item");

navItems.forEach((item) => {
  item.addEventListener("click", () => {
    const target = item.dataset.target;
    navItems.forEach((nav) => nav.classList.toggle("active", nav === item));
    views.forEach((view) => view.classList.toggle("active", view.dataset.view === target));
  });
});

function renderResult(result) {
  document.querySelector("#decisionMetric").textContent = result.decision || "Unknown";
  document.querySelector("#runtimeMetric").textContent = `${Math.round(result.elapsed_seconds || 0)}s`;
  document.querySelector("#marketReport").textContent = result.sections?.market || "No market report available.";
  document.querySelector("#finalReport").textContent = result.sections?.final || "No final decision available.";
}

function setStatus(message) {
  const status = document.querySelector("#statusText");
  if (status) status.textContent = message;
}

function renderSymbols(symbols = []) {
  if (!symbols.length) return "<span class=\"status-text\">No symbols resolved.</span>";
  return symbols
    .map(
      (symbol) =>
        `<span class="symbol-pill"><strong>${symbol.ticker}</strong>${symbol.company_name}<small>${symbol.exchange} · ${symbol.currency}</small></span>`
    )
    .join("");
}

function renderCopilotDraft(draft) {
  const panel = document.querySelector("#copilotDraft");
  if (!panel) return;
  lastCopilotDraft = draft;
  const range = [draft.start_date, draft.end_date].filter(Boolean).join(" → ") || "As-of workflow";
  const action =
    draft.intent === "add_to_watchlist"
      ? "<button type=\"button\" id=\"confirmWatchlist\">Add To Watchlist</button>"
      : draft.intent === "multi_compare"
        ? "<button type=\"button\" id=\"confirmCompare\">Confirm Compare</button>"
        : draft.intent === "single_analysis"
          ? "<button type=\"button\" id=\"confirmSingleAnalysis\">Start Analysis</button>"
          : "";
  panel.innerHTML = `
    <div class="draft-header">
      <span>${draft.intent}</span>
      <strong>${range}</strong>
    </div>
    <div class="symbol-list">${renderSymbols(draft.symbols)}</div>
    <p class="status-text">${draft.message}</p>
    <div class="draft-actions">${action}</div>
  `;
}

async function loadWatchlist() {
  const container = document.querySelector("#watchlistItems");
  if (!container || !authToken) return;
  try {
    const items = await apiFetch("/watchlist");
    container.innerHTML = items.length
      ? items
          .map(
            (item) =>
              `<div class="row-item"><span><strong>${item.ticker}</strong>${item.company_name}</span><small>${item.source}</small></div>`
          )
          .join("")
      : "<p class=\"status-text\">No confirmed watchlist items yet.</p>";
  } catch (error) {
    container.innerHTML = `<p class="status-text">Watchlist unavailable: ${error.message}</p>`;
  }
}

function renderCompareWorkflow(workflow) {
  const container = document.querySelector("#compareItems");
  if (!container) return;
  container.innerHTML = `
    <div class="row-item">
      <span><strong>${workflow.symbols.map((symbol) => symbol.ticker).join(" / ")}</strong>${workflow.start_date || "Open"} → ${workflow.end_date || "Latest"}</span>
      <small>${workflow.status}</small>
    </div>
  `;
}

async function apiFetch(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };
  if (authToken) headers.Authorization = `Bearer ${authToken}`;

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

async function loadPublicDemo() {
  try {
    const result = await fetch(`${API_BASE}/demo/reference`).then((response) => response.json());
    renderResult(result);
    setStatus("Loaded public demo from API.");
  } catch {
    renderResult(demoResult);
    setStatus("Showing local demo fallback.");
  }
}

document.querySelector("#loginForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  try {
    const payload = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(Object.fromEntries(form))
    }).then((response) => response.json());
    authToken = payload.access_token;
    localStorage.setItem("alphapilot_token", authToken);
    setStatus("Logged in.");
    await loadWatchlist();
    document.querySelector('[data-target="dashboard"]').click();
  } catch (error) {
    setStatus(`Login failed: ${error.message}`);
  }
});

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelector("#copilotMessage").value = button.dataset.prompt;
  });
});

document.querySelector("#copilotForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const draft = await apiFetch("/copilot/route", {
      method: "POST",
      body: JSON.stringify({ message: document.querySelector("#copilotMessage").value })
    });
    renderCopilotDraft(draft);
    setStatus("Workflow draft ready for confirmation.");
  } catch (error) {
    document.querySelector("#copilotDraft").innerHTML = `<p class="status-text">Login required or route failed: ${error.message}</p>`;
  }
});

document.querySelector("#copilotDraft").addEventListener("click", async (event) => {
  if (!lastCopilotDraft) return;
  if (event.target.id === "confirmWatchlist") {
    await Promise.all(
      lastCopilotDraft.symbols.map((symbol) =>
        apiFetch("/watchlist", {
          method: "POST",
          body: JSON.stringify({ ...symbol, source: "copilot" })
        })
      )
    );
    await loadWatchlist();
    setStatus("Watchlist updated.");
    document.querySelector('[data-target="watchlist"]').click();
  }
  if (event.target.id === "confirmCompare") {
    const workflow = await apiFetch("/compare", {
      method: "POST",
      body: JSON.stringify({
        symbols: lastCopilotDraft.symbols,
        start_date: lastCopilotDraft.start_date,
        end_date: lastCopilotDraft.end_date,
        analysis_anchor: lastCopilotDraft.analysis_anchor,
        source: "copilot"
      })
    });
    renderCompareWorkflow(workflow);
    setStatus("Compare workflow created.");
    document.querySelector('[data-target="compare"]').click();
  }
  if (event.target.id === "confirmSingleAnalysis") {
    const symbol = lastCopilotDraft.symbols[0];
    document.querySelector("#tickerInput").value = symbol.ticker;
    document.querySelector("#dateInput").value = lastCopilotDraft.analysis_anchor || document.querySelector("#dateInput").value;
    setStatus("Single analysis form prepared.");
    document.querySelector('[data-target="new-analysis"]').click();
  }
});

document.querySelector("#registerForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  try {
    await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(Object.fromEntries(form))
    });
    setStatus("Registered. You can log in now.");
  } catch (error) {
    setStatus(`Register failed: ${error.message}`);
  }
});

document.querySelector("#analysisForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = {
    ticker: document.querySelector("#tickerInput").value,
    trade_date: document.querySelector("#dateInput").value,
    mode: document.querySelector("#modeInput")?.value || "demo"
  };

  try {
    const job = await apiFetch("/analysis", {
      method: "POST",
      body: JSON.stringify(payload)
    });
    const detail = await apiFetch(`/analysis/${job.id}`);
    renderResult(detail.result || demoResult);
    setStatus(`Analysis ${job.status}.`);
    document.querySelector('[data-target="analysis-detail"]').click();
  } catch (error) {
    renderResult(demoResult);
    setStatus(`Using fallback demo: ${error.message}`);
    document.querySelector('[data-target="analysis-detail"]').click();
  }
});

loadPublicDemo();
loadWatchlist();
