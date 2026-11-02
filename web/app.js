const formatMs = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  const number = Number(value);
  if (number < 1000) return `${Math.round(number)} ms`;
  return `${(number / 1000).toFixed(number < 10000 ? 2 : 1)} s`;
};

const formatPercent = (value) => value === null || value === undefined ? "—" : `${Math.round(Number(value) * 100)}%`;

const $ = (selector) => document.querySelector(selector);

function evidenceLabel(source) {
  const labels = {
    "self-run": "Self-run",
    "community-run": "Community",
    "vendor-reported": "Vendor reported",
    "official-claim": "Official claim",
  };
  return labels[source] || source || "Unknown";
}

function renderStats(data) {
  $("#result-count").textContent = data.summary.result_count;
  $("#provider-count").textContent = data.summary.provider_count;
  $("#workload-count").textContent = data.summary.workload_count;
  $("#success-rate").textContent = formatPercent(data.summary.success_rate);
}

function renderFilters(data) {
  const select = $("#workload-filter");
  data.workloads.forEach((workload) => {
    const option = document.createElement("option");
    option.value = workload;
    option.textContent = workload;
    select.appendChild(option);
  });
}

function renderTable(records) {
  const body = $("#leaderboard-body");
  if (!records.length) {
    body.innerHTML = '<tr><td colspan="6" class="empty-state">No observations match these filters yet. Submit the first one through GitHub.</td></tr>';
    return;
  }
  body.innerHTML = records.map((record) => `
    <tr>
      <td><span class="provider-dot"></span>${record.provider}</td>
      <td>${record.workload}</td>
      <td>${formatPercent(record.success_rate)}</td>
      <td>${formatMs(record.avg_duration_ms)}</td>
      <td>${formatMs(record.p95_duration_ms)}</td>
      <td><span class="badge ${record.source === "official-claim" ? "muted" : ""}">${evidenceLabel(record.source)}</span></td>
    </tr>
  `).join("");
}

function renderCatalog(catalog) {
  const container = $("#provider-catalog");
  if (!catalog.length) {
    container.innerHTML = '<p class="empty-state">No providers have been added to the catalog yet.</p>';
    return;
  }
  container.innerHTML = catalog.map((provider, index) => `
    <article class="provider-card">
      <div class="provider-card-top">
        <div><span class="provider-index">${String(index + 1).padStart(2, "0")}</span><h3>${provider.name}</h3></div>
        <a href="${provider.source_url}" target="_blank" rel="noreferrer" aria-label="Open ${provider.name} source">↗</a>
      </div>
      <p class="provider-category">${provider.category}</p>
      <dl>
        <div><dt>Model</dt><dd>${provider.model}</dd></div>
        <div><dt>Isolation</dt><dd>${provider.isolation}</dd></div>
        <div><dt>Lifecycle</dt><dd>${provider.lifecycle}</dd></div>
        <div><dt>Vendor-reported claim</dt><dd>${provider.startup_claim || "Not published"}</dd></div>
      </dl>
      <div class="provider-claims"><span>Published capabilities</span><ul>${provider.official_claims.map((claim) => `<li>${claim}</li>`).join("")}</ul></div>
      <div class="provider-card-footer"><a href="${provider.docs_url}" target="_blank" rel="noreferrer">Docs ↗</a><span>Checked ${provider.last_checked}</span></div>
    </article>
  `).join("");
}

function boot(data) {
  const hostParts = window.location.hostname.split(".");
  const pathParts = window.location.pathname.split("/").filter(Boolean);
  if (hostParts.length >= 3 && hostParts[hostParts.length - 2] === "github" && hostParts[hostParts.length - 1] === "io" && pathParts[0]) {
    const repoUrl = `https://github.com/${hostParts[0]}/${pathParts[0]}`;
    document.querySelectorAll(".repo-link").forEach((link) => { link.href = repoUrl; });
  }
  renderStats(data);
  renderFilters(data);
  renderCatalog(data.catalog || []);
  const update = () => {
    const workload = $("#workload-filter").value;
    const source = $("#source-filter").value;
    const filtered = data.records.filter((record) => (workload === "all" || record.workload === workload) && (source === "all" || record.source === source));
    renderTable(filtered);
  };
  $("#workload-filter").addEventListener("change", update);
  $("#source-filter").addEventListener("change", update);
  update();
}

fetch("./data/results.json", { cache: "no-store" })
  .then((response) => {
    if (!response.ok) throw new Error(`data request failed: ${response.status}`);
    return response.json();
  })
  .then(boot)
  .catch((error) => {
    console.error(error);
    renderTable([]);
  });

