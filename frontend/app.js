const API_BASE = localStorage.getItem("alphapilot_api_base") || "http://127.0.0.1:8000";

const demoResult = {
  decision: "Overweight",
  elapsed_seconds: 267,
  sections: {
    market: "Market analysis is available from the saved Phase 1 NVDA smoke run. Connect the API to load the full report in live mode.",
    final: "Final decision: Overweight. This sample is presented for product demonstration only and is not financial advice."
  }
};

let authToken = localStorage.getItem("alphapilot_token") || "";

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
    document.querySelector('[data-target="dashboard"]').click();
  } catch (error) {
    setStatus(`Login failed: ${error.message}`);
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
