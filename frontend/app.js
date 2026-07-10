const API_BASE = localStorage.getItem("alphapilot_api_base") || window.location.origin;

const ANALYSIS_STAGES = [
  { key: "queued", label: "Ticker" },
  { key: "running", label: "Market data" },
  { key: "market", label: "Analyst" },
  { key: "debate", label: "Debate" },
  { key: "risk", label: "Risk" },
  { key: "final", label: "Final" }
];

const COMPARE_STAGES = [
  { key: "ticker", label: "Ticker" },
  { key: "data", label: "Data" },
  { key: "per_stock", label: "Per-stock analysis" },
  { key: "cross_stock", label: "Cross-stock comparison" },
  { key: "final", label: "Final summary" }
];

const TRANSLATIONS = {
  en: {
    dashboard: "Dashboard",
    analysis: "Analysis",
    compare: "Compare",
    titleDashboard: "Research command center",
    titleAnalysis: "Analysis workspace",
    titleCompare: "Compare workspace",
    titleUsers: "Manage Users",
    login: "Login",
    logout: "Logout",
    manageUsers: "Manage Users",
    quotaTitle: "Daily quota",
    quotaLogin: "Sign in required",
    quotaLoginHint: "Login to run live workflows.",
    adminQuota: "Admin access",
    adminQuotaHint: "Unlimited daily workflow quota. System safety limits still apply.",
    guideTitle: "How to use AlphaPilot",
    guideSteps:
      "<li><strong>Describe your research goal in Copilot.</strong> Ask in natural language, for example: \"Compare Tesla and AMD from the start of 2024 to now\".</li><li><strong>Confirm the interpreted workflow.</strong> AlphaPilot resolves tickers, dates, and whether the request belongs in Analysis or Compare.</li><li><strong>Follow progress in Analysis or Compare.</strong> After confirmation, the workflow starts automatically and shows stage updates.</li><li><strong>Read the final report.</strong> Reports are research assistance only. They are not financial advice and AlphaPilot does not execute trades.</li>",
    adminGuide:
      "<strong>Admin tools.</strong> Use Manage Users to review registered users, enable or disable accounts, and adjust regular-user quota settings.",
    copilotHint: "Login, then describe the research workflow you want to run.",
    statusDefault: "Describe a research request in Copilot, then confirm the interpreted analysis draft.",
    noRecent: "No recent workflow loaded.",
    noReport: "No report loaded.",
    reportGenerating: "Chinese report is not available yet. The English source report remains the canonical version.",
    stillRunning: "Still running. Waiting for next worker update.",
    loggedIn: "Logged in.",
    loggedOut: "Logged out."
  },
  zh: {
    dashboard: "仪表盘",
    analysis: "分析",
    compare: "对比",
    titleDashboard: "研究指令中心",
    titleAnalysis: "分析工作台",
    titleCompare: "对比工作台",
    titleUsers: "用户管理",
    login: "登录",
    logout: "退出登录",
    manageUsers: "管理用户",
    quotaTitle: "每日额度",
    quotaLogin: "需要登录",
    quotaLoginHint: "登录后可运行 live workflow。",
    adminQuota: "Admin access",
    adminQuotaHint: "Admin 不受每日 workflow 额度限制，但仍受系统安全限制保护。",
    guideTitle: "如何使用 AlphaPilot",
    guideSteps:
      "<li><strong>在 Copilot 里描述研究目标。</strong> 可以直接输入自然语言，例如：“比较 Tesla 和 AMD 从 2024 年初到现在的表现”。</li><li><strong>确认系统解析出的 workflow。</strong> AlphaPilot 会识别股票、日期，以及请求应进入 Analysis 还是 Compare。</li><li><strong>在 Analysis 或 Compare 跟踪进度。</strong> 确认后 workflow 会自动启动，并显示阶段进展。</li><li><strong>阅读最终报告。</strong> 报告只用于投资研究辅助，不构成投资建议，AlphaPilot 也不会执行交易。</li>",
    adminGuide:
      "<strong>Admin tools.</strong> 使用 Manage Users 查看注册用户、启用或禁用账号，并调整普通用户额度。",
    copilotHint: "登录后，在这里描述你想运行的研究 workflow。",
    statusDefault: "在 Copilot 中描述研究请求，然后确认系统解析出的分析草稿。",
    noRecent: "暂无最近 workflow。",
    noReport: "暂无报告。",
    reportGenerating: "中文报告暂不可用。英文原始报告仍是默认和最准确版本。",
    stillRunning: "仍在运行，等待 worker 的下一条更新。",
    loggedIn: "已登录。",
    loggedOut: "已退出登录。"
  }
};

const demoResult = {
  decision: "Demo result",
  elapsed_seconds: 267,
  sections: {
    market: "Saved NVDA Phase 1 demo is available for public inspection.",
    final: "Demo result only. Live analysis requires login, quota, and confirmation."
  }
};

let authToken = localStorage.getItem("alphapilot_token") || "";
let currentUser = null;
let lastCopilotDraft = null;
let activePoll = null;
let activeTimer = null;
let currentReport = { en: "", zh: "", status: "empty" };
let reportDisplayLanguage = "en";
let compareReportDisplayLanguage = "en";
let uiLocale = localStorage.getItem("alphapilot_ui_locale") || "en";
let activeView = "dashboard";

const views = document.querySelectorAll(".view");
const navItems = document.querySelectorAll(".nav-item");

function t(key) {
  return TRANSLATIONS[uiLocale][key] || TRANSLATIONS.en[key] || key;
}

function setText(selector, value) {
  const node = document.querySelector(selector);
  if (node) node.textContent = value;
}

function renderDashboardGuide() {
  setText("#dashboardGuideTitle", t("guideTitle"));
  document.querySelector("#dashboardGuideSteps").innerHTML = t("guideSteps");
  const adminGuide = document.querySelector("#adminGuide");
  adminGuide.innerHTML = t("adminGuide");
  adminGuide.hidden = currentUser?.role !== "admin";
}

function applyLocale() {
  document.querySelector('[data-target="dashboard"]').textContent = t("dashboard");
  document.querySelector('[data-target="analysis"]').textContent = t("analysis");
  document.querySelector('[data-target="compare"]').textContent = t("compare");
  setText("#localeToggle", uiLocale === "en" ? "EN / 中文" : "中文 / EN");
  setText("#accountButton", t("login"));
  setText("#logoutAction", t("logout"));
  setText("#manageUsersAction", t("manageUsers"));
  setText("#quotaTitle", t("quotaTitle"));
  setText("#workspaceTitle", viewTitle(activeView));
  renderDashboardGuide();
  updateAccountArea();
}

function setLocale(locale) {
  uiLocale = locale;
  localStorage.setItem("alphapilot_ui_locale", uiLocale);
  applyLocale();
}

function viewTitle(target) {
  if (target === "analysis") return t("titleAnalysis");
  if (target === "compare") return t("titleCompare");
  if (target === "manage-users") return t("titleUsers");
  return t("titleDashboard");
}

function showView(target) {
  activeView = target;
  navItems.forEach((nav) => nav.classList.toggle("active", nav.dataset.target === target));
  views.forEach((view) => view.classList.toggle("active", view.dataset.view === target));
  setText("#workspaceTitle", viewTitle(target));
}

navItems.forEach((item) => {
  item.addEventListener("click", () => showView(item.dataset.target));
});

function setStatus(message) {
  const status = document.querySelector("#statusText");
  if (status) status.textContent = message;
}

function setWorkspaceState(message, tone = "") {
  const state = document.querySelector("#workspaceState");
  if (!state) return;
  state.textContent = message;
  state.className = tone;
}

function parseTickers(value) {
  return value
    .split(/[\s,，、;；]+/)
    .map((ticker) => ticker.trim().toUpperCase())
    .filter(Boolean);
}

function escapeHtml(value = "") {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll("\"", "&quot;")
    .replaceAll("'", "&#039;");
}

function inlineMarkdown(value) {
  return value
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`(.+?)`/g, "<code>$1</code>");
}

function renderTable(lines) {
  const rows = lines.map((line) =>
    line
      .trim()
      .replace(/^\|/, "")
      .replace(/\|$/, "")
      .split("|")
      .map((cell) => inlineMarkdown(cell.trim()))
  );
  const head = rows[0] || [];
  const body = rows.slice(2);
  return `<table><thead><tr>${head.map((cell) => `<th>${cell}</th>`).join("")}</tr></thead><tbody>${body
    .map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`)
    .join("")}</tbody></table>`;
}

function renderMarkdown(markdown = "") {
  const safe = escapeHtml(markdown || "");
  const lines = safe.split(/\r?\n/);
  const blocks = [];
  let index = 0;
  while (index < lines.length) {
    const line = lines[index];
    if (!line.trim()) {
      index += 1;
      continue;
    }
    if (line.trim().startsWith("```")) {
      const code = [];
      index += 1;
      while (index < lines.length && !lines[index].trim().startsWith("```")) {
        code.push(lines[index]);
        index += 1;
      }
      index += 1;
      blocks.push(`<pre><code>${code.join("\n")}</code></pre>`);
      continue;
    }
    if (/^\|.+\|$/.test(line.trim()) && index + 1 < lines.length && /^\|?\s*:?-+:?\s*\|/.test(lines[index + 1].trim())) {
      const tableLines = [line, lines[index + 1]];
      index += 2;
      while (index < lines.length && /^\|.+\|$/.test(lines[index].trim())) {
        tableLines.push(lines[index]);
        index += 1;
      }
      blocks.push(renderTable(tableLines));
      continue;
    }
    if (/^#{1,4}\s+/.test(line)) {
      const depth = line.match(/^#+/)[0].length;
      blocks.push(`<h${depth}>${inlineMarkdown(line.replace(/^#{1,4}\s+/, ""))}</h${depth}>`);
      index += 1;
      continue;
    }
    if (/^---+$/.test(line.trim())) {
      blocks.push("<hr>");
      index += 1;
      continue;
    }
    if (/^>\s+/.test(line)) {
      blocks.push(`<blockquote>${inlineMarkdown(line.replace(/^>\s+/, ""))}</blockquote>`);
      index += 1;
      continue;
    }
    if (/^[-*]\s+/.test(line)) {
      const items = [];
      while (index < lines.length && /^[-*]\s+/.test(lines[index])) {
        items.push(`<li>${inlineMarkdown(lines[index].replace(/^[-*]\s+/, ""))}</li>`);
        index += 1;
      }
      blocks.push(`<ul>${items.join("")}</ul>`);
      continue;
    }
    if (/^\d+\.\s+/.test(line)) {
      const items = [];
      while (index < lines.length && /^\d+\.\s+/.test(lines[index])) {
        items.push(`<li>${inlineMarkdown(lines[index].replace(/^\d+\.\s+/, ""))}</li>`);
        index += 1;
      }
      blocks.push(`<ol>${items.join("")}</ol>`);
      continue;
    }
    const paragraph = [line];
    index += 1;
    while (index < lines.length && lines[index].trim() && !/^#{1,4}\s+|^[-*]\s+|^\d+\.\s+|^>\s+|^\|.+\|$|^---+$|^```/.test(lines[index])) {
      paragraph.push(lines[index]);
      index += 1;
    }
    blocks.push(`<p>${inlineMarkdown(paragraph.join(" "))}</p>`);
  }
  return blocks.join("");
}

function renderSymbols(symbols = []) {
  if (!symbols.length) return "<span class=\"status-text\">No symbols resolved.</span>";
  return symbols
    .map(
      (symbol) =>
        `<span class="symbol-pill"><strong>${escapeHtml(symbol.ticker)}</strong>${escapeHtml(symbol.company_name)}<small>${escapeHtml(symbol.exchange)} · ${escapeHtml(symbol.currency)}</small></span>`
    )
    .join("");
}

function draftSymbolKey(symbol) {
  return String(symbol?.ticker || "").toUpperCase();
}

function symbolIsSelected(symbols = [], ticker) {
  const target = String(ticker || "").toUpperCase();
  return symbols.some((symbol) => draftSymbolKey(symbol) === target);
}

function renderDraftSymbols(symbols = []) {
  if (!symbols.length) return "<span class=\"status-text\">No symbols selected yet.</span>";
  return symbols
    .map(
      (symbol) => `
        <span class="symbol-pill draft-symbol-chip">
          <span><strong>${escapeHtml(symbol.ticker)}</strong>${escapeHtml(symbol.company_name)}<small>${escapeHtml(symbol.exchange)} · ${escapeHtml(symbol.currency)}</small></span>
          <button type="button" class="chip-remove" data-remove-symbol="${escapeHtml(symbol.ticker)}" aria-label="Remove ${escapeHtml(symbol.ticker)}">&times;</button>
        </span>
      `
    )
    .join("");
}

function renderCandidateGroups(draft) {
  const groups = draft?.candidate_groups || [];
  const choiceGroups = groups.filter((group) => group.candidates?.length > 1);
  if (!choiceGroups.length) return "";
  return `
    <div class="candidate-groups">
      ${choiceGroups
        .map(
          (group) => `
            <div class="candidate-group">
              <strong>${escapeHtml(group.query)}</strong>
              <div class="candidate-options">
                ${group.candidates
                  .map((candidate) => {
                    const selected = symbolIsSelected(draft.symbols, candidate.ticker);
                    return `
                      <button type="button" class="candidate-option ${selected ? "selected" : ""}" data-candidate-query="${escapeHtml(group.query)}" data-candidate-ticker="${escapeHtml(candidate.ticker)}">
                        <span>${escapeHtml(candidate.ticker)}</span>
                        <small>${escapeHtml(candidate.company_name)}</small>
                      </button>
                    `;
                  })
                  .join("")}
              </div>
            </div>
          `
        )
        .join("")}
    </div>
  `;
}

function renderUnresolvedEntities(entities = []) {
  if (!entities.length) return "";
  return `
    <div class="unresolved-entities">
      <strong>Needs more detail</strong>
      <div>
        ${entities.map((entity) => `<span class="unresolved-chip">${escapeHtml(entity)}</span>`).join("")}
      </div>
    </div>
  `;
}

function removeDraftSymbol(ticker) {
  if (!lastCopilotDraft) return;
  const target = String(ticker || "").toUpperCase();
  lastCopilotDraft = {
    ...lastCopilotDraft,
    symbols: lastCopilotDraft.symbols.filter((symbol) => draftSymbolKey(symbol) !== target),
    requires_confirmation: true
  };
  renderCopilotDraft(lastCopilotDraft);
}

function selectDraftCandidate(query, ticker) {
  if (!lastCopilotDraft) return;
  const group = (lastCopilotDraft.candidate_groups || []).find((candidateGroup) => candidateGroup.query === query);
  const selected = group?.candidates?.find((candidate) => draftSymbolKey(candidate) === String(ticker || "").toUpperCase());
  if (!group || !selected) return;
  const groupTickers = new Set(group.candidates.map((candidate) => draftSymbolKey(candidate)));
  const nextSymbols = lastCopilotDraft.symbols.filter((symbol) => !groupTickers.has(draftSymbolKey(symbol)));
  if (!symbolIsSelected(nextSymbols, selected.ticker)) nextSymbols.push(selected);
  lastCopilotDraft = {
    ...lastCopilotDraft,
    symbols: nextSymbols,
    requires_confirmation: true
  };
  renderCopilotDraft(lastCopilotDraft);
}

function validateDraftBeforeConfirm(draft) {
  if (!draft) return "No draft to confirm.";
  if (draft.unresolved_entities?.length) return "Resolve or clarify the unresolved entities before confirming.";
  const symbols = draft.symbols || [];
  const unresolvedChoice = (draft.candidate_groups || []).find(
    (group) => group.candidates?.length > 1 && !group.candidates.some((candidate) => symbolIsSelected(symbols, candidate.ticker))
  );
  if (unresolvedChoice) return `Select the intended ticker for ${unresolvedChoice.query}.`;
  if (draft.intent === "compare" && (symbols.length < 2 || symbols.length > 5)) {
    return "Compare workflows need 2 to 5 selected stocks.";
  }
  if (draft.intent === "analysis" && symbols.length < 1) {
    return "Analysis workflows need at least one selected stock.";
  }
  return "";
}

function formatDuration(seconds) {
  if (!Number.isFinite(seconds) || seconds < 0) return "--";
  const rounded = Math.round(seconds);
  if (rounded < 60) return `${rounded}s`;
  const minutes = Math.floor(rounded / 60);
  const rest = rounded % 60;
  return rest ? `${minutes}m ${rest}s` : `${minutes}m`;
}

function secondsBetween(start, end) {
  const startTime = new Date(start).getTime();
  const endTime = new Date(end || Date.now()).getTime();
  if (!Number.isFinite(startTime) || !Number.isFinite(endTime)) return null;
  return Math.max(0, (endTime - startTime) / 1000);
}

function deriveRuntimeSeconds(job, result) {
  if (result?.elapsed_seconds) return Number(result.elapsed_seconds);
  if (job?.status === "completed") return secondsBetween(job.created_at, job.updated_at);
  return null;
}

function reportMarkdownFromResult(result) {
  const sections = result?.sections || {};
  const parts = [];
  if (sections.market) parts.push(`## Market report\n\n${sections.market}`);
  if (sections.sentiment) parts.push(`## Sentiment\n\n${sections.sentiment}`);
  if (sections.news) parts.push(`## News\n\n${sections.news}`);
  if (sections.fundamentals) parts.push(`## Fundamentals\n\n${sections.fundamentals}`);
  if (sections.investment) parts.push(`## Investment debate\n\n${sections.investment}`);
  if (sections.trader) parts.push(`## Trader plan\n\n${sections.trader}`);
  if (sections.final) parts.push(`## Final report\n\n${sections.final}`);
  return parts.join("\n\n---\n\n") || t("noReport");
}

function renderReport() {
  const selected = reportDisplayLanguage === "zh" ? currentReport.zh : currentReport.en;
  const text = selected || (reportDisplayLanguage === "zh" ? t("reportGenerating") : t("noReport"));
  document.querySelector("#reportRendered").innerHTML = renderMarkdown(text);
}

function renderCompareReportText(workflow) {
  const tickers = workflow.symbols.map((symbol) => symbol.ticker).join(" / ");
  return `# Compare workflow\n\n| Field | Value |\n|---|---|\n| Symbols | ${tickers} |\n| Start date | ${workflow.start_date || "Open"} |\n| End date | ${workflow.end_date || "Latest"} |\n| Status | ${workflow.status} |\n\nThis compare workflow is ready for cross-stock research. Final comparison reporting will use the same rendered report surface as Analysis.`;
}

function renderCompareReport(workflow) {
  const english = workflow ? renderCompareReportText(workflow) : t("noReport");
  const chinese = workflow
    ? `# 对比 workflow\n\n| 字段 | 内容 |\n|---|---|\n| 股票 | ${workflow.symbols.map((symbol) => symbol.ticker).join(" / ")} |\n| 开始日期 | ${workflow.start_date || "开放区间"} |\n| 结束日期 | ${workflow.end_date || "最新"} |\n| 状态 | ${workflow.status} |\n\n该 compare workflow 已创建，可用于后续横向研究。`
    : t("noReport");
  const selected = compareReportDisplayLanguage === "zh" ? chinese : english;
  document.querySelector("#compareReport").innerHTML = renderMarkdown(selected);
}

function renderResult(result, job = null) {
  const decision = result.decision || "No current decision";
  document.querySelector("#decisionMetric").textContent = decision;
  document.querySelector("#runtimeMetric").textContent = formatDuration(deriveRuntimeSeconds(job, result));
  currentReport = {
    en: reportMarkdownFromResult(result),
    zh: result.localized_sections?.zh?.report || result.localized_sections?.zh?.final || "",
    status: result.localized_sections?.zh ? "cached" : "missing"
  };
  renderReport();
  document.querySelector("#reportState").textContent = decision || "Completed";
}

function stageIndex(stages, stageKey) {
  const index = stages.findIndex((stage) => stage.key === stageKey);
  return index >= 0 ? index : 0;
}

function renderStageBar(container, stages, activeKey, done) {
  const activeIndex = done ? stages.length - 1 : stageIndex(stages, activeKey);
  container.innerHTML = stages
    .map((stage, index) => {
      const state = done || index < activeIndex ? "complete" : index === activeIndex ? "active" : "pending";
      return `<span class="stage-step ${state}"><i></i>${escapeHtml(stage.label)}</span>`;
    })
    .join("");
}

function renderProgressChrome(prefix, stages, job, events = []) {
  const stateNode = document.querySelector(`#${prefix}ProgressState`);
  const currentStageNode = document.querySelector(`#${prefix}CurrentStage`);
  const elapsedNode = document.querySelector(`#${prefix}Elapsed`);
  const ageNode = document.querySelector(`#${prefix}UpdateAge`);
  const statusNode = document.querySelector(`#${prefix}ProgressStatus`);
  const stageBar = document.querySelector(`#${prefix}StageBar`);
  if (!stateNode || !currentStageNode || !elapsedNode || !ageNode || !statusNode || !stageBar) return;

  const latest = events[events.length - 1];
  const status = job?.status || "idle";
  const activeKey = latest?.stage_key || (status === "queued" ? "queued" : "ticker");
  const done = ["completed", "failed", "deleted"].includes(status);
  const elapsed = job ? deriveRuntimeSeconds(job, null) || secondsBetween(job.created_at, done ? job.updated_at : Date.now()) : null;
  const age = latest ? secondsBetween(latest.created_at, Date.now()) : null;

  stateNode.textContent = status;
  currentStageNode.textContent = latest?.stage_label || (job ? status : "No active workflow");
  elapsedNode.textContent = formatDuration(elapsed);
  ageNode.textContent = age === null ? "--" : `${formatDuration(age)} ago`;
  statusNode.querySelector(".live-dot").className = `live-dot ${["queued", "running"].includes(status) ? "running" : done ? "done" : "idle"}`;
  renderStageBar(stageBar, stages, activeKey, done);
}

function renderProgressEvents(events = [], job = null) {
  const container = document.querySelector("#analysisProgress");
  if (!container) return;
  renderProgressChrome("analysis", ANALYSIS_STAGES, job, events);
  if (!events.length) {
    container.innerHTML = "<p class=\"status-text\">Waiting for the worker to emit progress.</p>";
    return;
  }
  const latest = events[events.length - 1];
  const latestAge = secondsBetween(latest.created_at, Date.now());
  const liveness =
    job && ["queued", "running"].includes(job.status) && latestAge > 60
      ? `<p class="status-text liveness-note">${t("stillRunning")}</p>`
      : "";
  container.innerHTML =
    events
      .map((event, index) => {
        const current = index === events.length - 1;
        const tone = event.status === "failed" ? "danger" : event.status === "completed" ? "positive" : "warning";
        return `
          <div class="progress-event">
            <div class="event-meta">${new Date(event.created_at).toLocaleString()}</div>
            <strong class="${tone}">${escapeHtml(event.stage_label)}</strong>
            <span class="${current ? "typewriter" : ""}">${escapeHtml(event.summary || event.status)}</span>
          </div>
        `;
      })
      .join("") + liveness;
}

function renderCompareProgress(workflow) {
  const events = workflow
    ? [
        { stage_key: "ticker", stage_label: "Ticker", status: "completed", summary: "Symbols resolved for comparison.", created_at: workflow.created_at },
        { stage_key: "final", stage_label: "Final summary", status: "completed", summary: "Compare workflow is ready for review.", created_at: workflow.updated_at }
      ]
    : [];
  const jobLike = workflow
    ? { status: workflow.status === "draft" ? "completed" : workflow.status, created_at: workflow.created_at, updated_at: workflow.updated_at }
    : null;
  renderProgressChrome("compare", COMPARE_STAGES, jobLike, events);
  const container = document.querySelector("#compareProgress");
  container.innerHTML = events.length
    ? events
        .map(
          (event) => `<div class="progress-event"><div class="event-meta">${new Date(event.created_at).toLocaleString()}</div><strong class="positive">${event.stage_label}</strong><span>${event.summary}</span></div>`
        )
        .join("")
    : "<p class=\"status-text\">Open or create a compare workflow to see stage progress.</p>";
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
  if (response.status === 204) return null;
  return response.json();
}

async function loadPublicDemo() {
  try {
    await fetch(`${API_BASE}/demo/reference`).then((response) => response.json());
    setStatus("Public demo reference is available.");
  } catch {
    setStatus(demoResult.sections.final);
  }
}

function updateAccountArea() {
  const accountButton = document.querySelector("#accountButton");
  const logoutAction = document.querySelector("#logoutAction");
  const accountLabel = document.querySelector("#accountLabel");
  const manageUsersAction = document.querySelector("#manageUsersAction");
  const quotaText = document.querySelector("#quotaText");
  const quotaHint = document.querySelector("#quotaHint");
  const quotaBar = document.querySelector("#quotaBar");

  if (!currentUser) {
    accountButton.hidden = false;
    logoutAction.hidden = true;
    accountLabel.hidden = true;
    manageUsersAction.hidden = true;
    accountButton.textContent = t("login");
    quotaText.textContent = t("quotaLogin");
    quotaHint.textContent = t("quotaLoginHint");
    quotaBar.style.width = "0%";
    renderDashboardGuide();
    return;
  }

  accountButton.hidden = true;
  logoutAction.hidden = false;
  accountLabel.hidden = false;
  accountLabel.textContent = currentUser.display_name || currentUser.email;
  manageUsersAction.hidden = currentUser.role !== "admin";

  if (currentUser.role === "admin") {
    quotaText.textContent = t("adminQuota");
    quotaHint.textContent = t("adminQuotaHint");
    quotaBar.style.width = "100%";
  } else {
    const quota = currentUser.quota || { used_today: 0, daily_limit: 0 };
    quotaText.textContent = `${quota.used_today} / ${quota.daily_limit}`;
    quotaHint.textContent = "Live workflows used today.";
    const percent = quota.daily_limit ? Math.min(100, Math.round((quota.used_today / quota.daily_limit) * 100)) : 0;
    quotaBar.style.width = `${percent}%`;
  }
  renderDashboardGuide();
}

async function loadCurrentUser() {
  if (!authToken) {
    currentUser = null;
    updateAccountArea();
    return null;
  }
  try {
    currentUser = await apiFetch("/me");
    updateAccountArea();
    await Promise.all([loadAnalysisHistory(), loadCompareHistory()]);
    return currentUser;
  } catch {
    authToken = "";
    localStorage.removeItem("alphapilot_token");
    currentUser = null;
    updateAccountArea();
    return null;
  }
}

function renderAnalysisHistory(jobs = []) {
  const container = document.querySelector("#analysisHistory");
  document.querySelector("#analysisHistoryCount").textContent = String(jobs.length);
  document.querySelector("#activityCount").textContent = String(jobs.length);
  if (!jobs.length) {
    container.innerHTML = "<p class=\"status-text\">No analysis history yet.</p>";
    document.querySelector("#recentActivity").innerHTML = `<p class="status-text">${t("noRecent")}</p>`;
    document.querySelector("#decisionMetric").textContent = "No active analysis";
    document.querySelector("#runtimeMetric").textContent = "--";
    return;
  }
  const rows = jobs
    .map(
      (job) =>
        `<div class="row-item">
          <button type="button" class="history-open" data-job-id="${job.id}">
            <span><strong>${escapeHtml(job.ticker)}</strong>${escapeHtml(job.trade_date)}</span>
            <small>${escapeHtml(job.status)}</small>
          </button>
          <button type="button" class="delete-action" data-delete-job-id="${job.id}" aria-label="Delete ${escapeHtml(job.ticker)} analysis">Delete</button>
        </div>`
    )
    .join("");
  container.innerHTML = rows;
  document.querySelector("#recentActivity").innerHTML = rows;
}

async function loadAnalysisHistory() {
  if (!authToken) return;
  try {
    renderAnalysisHistory(await apiFetch("/analysis"));
  } catch (error) {
    document.querySelector("#analysisHistory").innerHTML = `<p class="status-text">${escapeHtml(error.message)}</p>`;
  }
}

function renderCompareWorkflow(workflow) {
  const container = document.querySelector("#compareItems");
  if (!container) return;
  const row = `
    <div class="row-item">
      <button type="button" class="history-open" data-compare-id="${workflow.id}">
        <span><strong>${workflow.symbols.map((symbol) => escapeHtml(symbol.ticker)).join(" / ")}</strong>${escapeHtml(workflow.start_date || "Open")} to ${escapeHtml(workflow.end_date || "Latest")}</span>
        <small>${escapeHtml(workflow.status)}</small>
      </button>
      <button type="button" class="delete-action" data-delete-compare-id="${workflow.id}" aria-label="Delete compare workflow">Delete</button>
    </div>
  `;
  container.innerHTML = row + container.innerHTML.replace("<p class=\"status-text\">No compare workflows loaded.</p>", "");
  renderCompareProgress(workflow);
  renderCompareReport(workflow);
}

function renderCompareHistory(workflows = []) {
  const container = document.querySelector("#compareItems");
  document.querySelector("#compareHistoryCount").textContent = String(workflows.length);
  container.innerHTML = workflows.length
    ? workflows
        .map(
          (workflow) => `
            <div class="row-item">
              <button type="button" class="history-open" data-compare-id="${workflow.id}">
                <span><strong>${workflow.symbols.map((symbol) => escapeHtml(symbol.ticker)).join(" / ")}</strong>${escapeHtml(workflow.start_date || "Open")} to ${escapeHtml(workflow.end_date || "Latest")}</span>
                <small>${escapeHtml(workflow.status)}</small>
              </button>
              <button type="button" class="delete-action" data-delete-compare-id="${workflow.id}" aria-label="Delete compare workflow">Delete</button>
            </div>
          `
        )
        .join("")
    : "<p class=\"status-text\">No compare workflows loaded.</p>";
}

async function loadCompareHistory() {
  if (!authToken) return;
  try {
    renderCompareHistory(await apiFetch("/compare"));
  } catch (error) {
    document.querySelector("#compareItems").innerHTML = `<p class="status-text">${escapeHtml(error.message)}</p>`;
  }
}

async function loadCompareDetail(workflowId) {
  const workflow = await apiFetch(`/compare/${workflowId}`);
  renderCompareProgress(workflow);
  renderCompareReport(workflow);
  return workflow;
}

async function renderJobDetail(jobId) {
  const detail = await apiFetch(`/analysis/${jobId}`);
  const progress = await apiFetch(`/analysis/${jobId}/progress`);
  renderProgressEvents(progress, detail.job);
  document.querySelector("#analysisProgressState").textContent = detail.job.status;
  if (detail.result) {
    renderResult(detail.result, detail.job);
    setWorkspaceState("Completed", "positive");
  } else {
    document.querySelector("#reportState").textContent = detail.job.status;
    currentReport = {
      en: "The worker is still building this report.\n\nInterim stage updates appear in the progress panel.",
      zh: "",
      status: "missing"
    };
    renderReport();
    setWorkspaceState(detail.job.status, "warning");
  }
  return detail;
}

async function pollAnalysisJob(jobId) {
  if (activePoll) clearTimeout(activePoll);
  if (activeTimer) clearInterval(activeTimer);
  activeTimer = setInterval(() => renderJobDetail(jobId).catch(() => {}), 10000);
  let detail;
  try {
    detail = await renderJobDetail(jobId);
  } catch (error) {
    if (error.message.includes("not found") || error.message.includes("404")) {
      await loadAnalysisHistory();
      setWorkspaceState("Deleted", "warning");
      return;
    }
    throw error;
  }
  if (["queued", "running"].includes(detail.job.status)) {
    activePoll = setTimeout(() => pollAnalysisJob(jobId), 2500);
  } else {
    if (activeTimer) clearInterval(activeTimer);
    await loadAnalysisHistory();
    await loadCurrentUser();
  }
}

async function createAnalysisJobs({ tickers, tradeDate, mode = "live", selectedAnalysts = ["market"] }) {
  if (!tickers.length) throw new Error("Please provide at least one ticker.");
  const jobs = [];
  for (const ticker of tickers) {
    const job = await apiFetch("/analysis", {
      method: "POST",
      body: JSON.stringify({
        ticker,
        trade_date: tradeDate,
        mode,
        selected_analysts: selectedAnalysts
      })
    });
    jobs.push(job);
  }
  await loadAnalysisHistory();
  showView("analysis");
  await pollAnalysisJob(jobs[0].id);
  return jobs;
}

async function deleteAnalysisJob(jobId) {
  await apiFetch(`/analysis/${jobId}`, { method: "DELETE" });
  if (activePoll) clearTimeout(activePoll);
  if (activeTimer) clearInterval(activeTimer);
  await loadAnalysisHistory();
  renderProgressEvents([], null);
  document.querySelector("#analysisProgressState").textContent = "Deleted";
  document.querySelector("#reportState").textContent = "Deleted";
  currentReport = { en: "This analysis was removed from history.", zh: "", status: "missing" };
  renderReport();
  setWorkspaceState("Deleted", "warning");
  setStatus("Analysis history item deleted.");
}

async function deleteCompareWorkflow(workflowId) {
  await apiFetch(`/compare/${workflowId}`, { method: "DELETE" });
  await loadCompareHistory();
  renderCompareProgress(null);
  renderCompareReport(null);
  setStatus("Compare history item deleted.");
}

function renderCopilotDraft(draft) {
  const panel = document.querySelector("#copilotDraft");
  lastCopilotDraft = draft;
  const range = [draft.start_date, draft.end_date].filter(Boolean).join(" to ") || "As-of workflow";
  const action = draft.requires_confirmation ? "<button type=\"button\" id=\"confirmDraft\">Confirm</button>" : "";
  panel.innerHTML = `
    <div class="draft-header">
      <span>${escapeHtml(draft.intent)}</span>
      <strong>${escapeHtml(range)}</strong>
    </div>
    <div class="symbol-list">${renderDraftSymbols(draft.symbols)}</div>
    ${renderCandidateGroups(draft)}
    ${renderUnresolvedEntities(draft.unresolved_entities)}
    <p class="status-text">${escapeHtml(draft.message)}</p>
    <div class="draft-actions">${action}</div>
  `;
}

function renderAdminUsers(users = []) {
  document.querySelector("#adminUsersCount").textContent = String(users.length);
  const list = document.querySelector("#adminUsersList");
  list.innerHTML = users.length
    ? users
        .map(
          (user) => `
            <div class="admin-user-row">
              <span><strong>${escapeHtml(user.display_name || user.email)}</strong><small>${escapeHtml(user.email)} · ${escapeHtml(user.role)} · ${user.is_active ? "active" : "disabled"}</small></span>
              <label>Quota <input type="number" min="0" max="100" value="${user.quota.daily_limit}" data-quota-user-id="${user.id}" ${user.role === "admin" ? "disabled" : ""}></label>
              <button type="button" class="ghost-action" data-active-user-id="${user.id}" data-next-active="${!user.is_active}">${user.is_active ? "Disable" : "Enable"}</button>
              <button type="button" data-save-quota-id="${user.id}" ${user.role === "admin" ? "disabled" : ""}>Save</button>
            </div>
          `
        )
        .join("")
    : "<p class=\"status-text\">No users loaded.</p>";
}

async function loadAdminUsers() {
  const users = await apiFetch("/admin/users");
  renderAdminUsers(users);
}

async function logout() {
  authToken = "";
  currentUser = null;
  localStorage.removeItem("alphapilot_token");
  updateAccountArea();
  setStatus(t("loggedOut"));
  showView("auth");
}

document.querySelector("#localeToggle").addEventListener("click", () => setLocale(uiLocale === "en" ? "zh" : "en"));

document.querySelector("#accountButton").addEventListener("click", () => showView("auth"));
document.querySelector("#logoutAction").addEventListener("click", logout);
document.querySelector("#manageUsersAction").addEventListener("click", async () => {
  showView("manage-users");
  try {
    await loadAdminUsers();
  } catch (error) {
    document.querySelector("#adminUsersList").innerHTML = `<p class="status-text">${escapeHtml(error.message)}</p>`;
  }
});

document.querySelector("#adminUsersList").addEventListener("click", async (event) => {
  const activeButton = event.target.closest("[data-active-user-id]");
  const saveButton = event.target.closest("[data-save-quota-id]");
  try {
    if (activeButton) {
      await apiFetch(`/admin/users/${activeButton.dataset.activeUserId}`, {
        method: "PATCH",
        body: JSON.stringify({ is_active: activeButton.dataset.nextActive === "true" })
      });
      await loadAdminUsers();
    }
    if (saveButton) {
      const input = document.querySelector(`[data-quota-user-id="${saveButton.dataset.saveQuotaId}"]`);
      await apiFetch(`/admin/users/${saveButton.dataset.saveQuotaId}`, {
        method: "PATCH",
        body: JSON.stringify({ daily_limit: Number(input.value) })
      });
      await loadAdminUsers();
    }
  } catch (error) {
    setStatus(`Admin update failed: ${error.message}`);
  }
});

document.querySelector("#reportLanguageToggle").addEventListener("change", (event) => {
  reportDisplayLanguage = event.target.value;
  renderReport();
});

document.querySelector("#compareReportLanguageToggle").addEventListener("change", (event) => {
  compareReportDisplayLanguage = event.target.value;
  const selected = document.querySelector("[data-compare-id].history-open");
  if (selected) loadCompareDetail(selected.dataset.compareId).catch(() => renderCompareReport(null));
});

document.querySelector("#loginForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  try {
    const payload = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(Object.fromEntries(form))
    }).then((response) => response.json());
    if (!payload.access_token) throw new Error(payload.detail || "Login failed");
    authToken = payload.access_token;
    localStorage.setItem("alphapilot_token", authToken);
    await loadCurrentUser();
    setStatus(t("loggedIn"));
    showView("dashboard");
  } catch (error) {
    setStatus(`Login failed: ${error.message}`);
  }
});

document.querySelector("#registerForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  try {
    const response = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(Object.fromEntries(form))
    });
    if (!response.ok) throw new Error((await response.json()).detail || `HTTP ${response.status}`);
    setStatus("Registered. You can log in now.");
  } catch (error) {
    setStatus(`Register failed: ${error.message}`);
  }
});

document.querySelector("#copilotForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const draft = await apiFetch("/copilot/route", {
      method: "POST",
      body: JSON.stringify({ message: document.querySelector("#copilotMessage").value })
    });
    renderCopilotDraft(draft);
    setStatus("Draft ready. Confirm it or correct the request in the same box.");
  } catch (error) {
    document.querySelector("#copilotDraft").innerHTML = `<p class="status-text">Login required or route failed: ${escapeHtml(error.message)}</p>`;
  }
});

document.querySelector("#copilotDraft").addEventListener("click", async (event) => {
  const removeButton = event.target.closest("[data-remove-symbol]");
  if (removeButton) {
    removeDraftSymbol(removeButton.dataset.removeSymbol);
    return;
  }
  const candidateButton = event.target.closest("[data-candidate-query][data-candidate-ticker]");
  if (candidateButton) {
    selectDraftCandidate(candidateButton.dataset.candidateQuery, candidateButton.dataset.candidateTicker);
    return;
  }
  if (event.target.id !== "confirmDraft" || !lastCopilotDraft) return;
  const validationError = validateDraftBeforeConfirm(lastCopilotDraft);
  if (validationError) {
    setStatus(validationError);
    return;
  }
  try {
    if (lastCopilotDraft.intent === "compare") {
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
      await loadCompareHistory();
      showView("compare");
      setStatus("Compare workflow created.");
      return;
    }
    await createAnalysisJobs({
      tickers: lastCopilotDraft.symbols.map((symbol) => symbol.ticker),
      tradeDate: lastCopilotDraft.analysis_anchor || new Date().toISOString().slice(0, 10),
      mode: "live",
      selectedAnalysts: ["market"]
    });
    setStatus("Analysis workflow started.");
  } catch (error) {
    setStatus(`Confirmation failed: ${error.message}`);
  }
});

document.querySelector("#analysisForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await createAnalysisJobs({
      tickers: parseTickers(document.querySelector("#tickerInput").value),
      tradeDate: document.querySelector("#dateInput").value,
      mode: document.querySelector("#modeInput").value,
      selectedAnalysts: document.querySelector("#analystInput").value.split(",")
    });
  } catch (error) {
    setStatus(`Analysis failed to start: ${error.message}`);
  }
});

document.querySelector("#compareForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const symbols = parseTickers(document.querySelector("#compareTickerInput").value).map((ticker) => ({
      ticker,
      company_name: ticker,
      market: "US",
      exchange: "NASDAQ",
      currency: "USD"
    }));
    const workflow = await apiFetch("/compare", {
      method: "POST",
      body: JSON.stringify({
        symbols,
        start_date: document.querySelector("#compareStartInput").value,
        end_date: document.querySelector("#compareEndInput").value,
        analysis_anchor: document.querySelector("#compareEndInput").value,
        source: "manual"
      })
    });
    renderCompareWorkflow(workflow);
    await loadCompareHistory();
    setStatus("Compare workflow created.");
  } catch (error) {
    setStatus(`Compare failed: ${error.message}`);
  }
});

document.querySelector("#analysisHistory").addEventListener("click", (event) => {
  const deleteButton = event.target.closest("[data-delete-job-id]");
  if (deleteButton) {
    deleteAnalysisJob(deleteButton.dataset.deleteJobId).catch((error) => setStatus(`Delete failed: ${error.message}`));
    return;
  }
  const row = event.target.closest("[data-job-id]");
  if (row) pollAnalysisJob(row.dataset.jobId);
});

document.querySelector("#recentActivity").addEventListener("click", (event) => {
  const deleteButton = event.target.closest("[data-delete-job-id]");
  if (deleteButton) {
    deleteAnalysisJob(deleteButton.dataset.deleteJobId).catch((error) => setStatus(`Delete failed: ${error.message}`));
    return;
  }
  const row = event.target.closest("[data-job-id]");
  if (row) {
    showView("analysis");
    pollAnalysisJob(row.dataset.jobId);
  }
});

document.querySelector("#compareItems").addEventListener("click", (event) => {
  const deleteButton = event.target.closest("[data-delete-compare-id]");
  if (deleteButton) {
    deleteCompareWorkflow(deleteButton.dataset.deleteCompareId).catch((error) => setStatus(`Delete failed: ${error.message}`));
    return;
  }
  const row = event.target.closest("[data-compare-id]");
  if (row) loadCompareDetail(row.dataset.compareId).catch((error) => setStatus(`Compare load failed: ${error.message}`));
});

applyLocale();
renderProgressChrome("analysis", ANALYSIS_STAGES, null, []);
renderProgressChrome("compare", COMPARE_STAGES, null, []);
renderReport();
renderCompareReport(null);
loadPublicDemo();
loadCurrentUser();
