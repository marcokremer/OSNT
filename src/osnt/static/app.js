const $ = (id) => document.getElementById(id);
const companySelect = $("company");
const focusSelect = $("focus");
const searchInput = $("q");
const statusEl = $("status");

const LABELS = {};

function setStatus(text, show = true) {
  statusEl.hidden = !show;
  statusEl.textContent = text || "";
}

async function api(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${body.slice(0, 200)}`);
  }
  return res.json();
}

function fmtEur(value) {
  if (value === null || value === undefined || value === "") return "—";
  const n = Number(value);
  if (!Number.isFinite(n) || n <= 1) return "—";
  return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(n);
}

function chips(tags) {
  return (tags || [])
    .map((t) => {
      const focus = t === "ai" || t === "data_platform";
      return `<span class="chip${focus ? " focus" : ""}">${t}</span>`;
    })
    .join("");
}

function companyQuery() {
  const params = new URLSearchParams();
  if (companySelect.value) params.set("company", companySelect.value);
  if (searchInput.value.trim()) params.set("q", searchInput.value.trim());
  if (focusSelect.value === "focus") params.set("focus", "true");
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

function renderKpis(stats) {
  $("kpis").innerHTML = [
    ["Vergaben", stats.notices],
    ["Kunden", stats.customers],
    ["Personen", stats.people],
    ["KI / Plattform", (stats.by_tag?.ai || 0) + (stats.by_tag?.data_platform || 0)],
  ]
    .map(
      ([label, value]) =>
        `<div class="kpi"><b>${value ?? 0}</b><span>${label}</span></div>`
    )
    .join("");
}

function renderBars(stats) {
  const entries = Object.entries(stats.by_company || {});
  const max = Math.max(1, ...entries.map(([, n]) => n));
  $("bars").innerHTML = entries
    .sort((a, b) => b[1] - a[1])
    .map(([id, n]) => {
      const pct = Math.round((n / max) * 100);
      return `<div class="bar-row"><span>${LABELS[id] || id}</span>
        <div class="bar-track"><div class="bar-fill" style="width:${pct}%"></div></div>
        <span>${n}</span></div>`;
    })
    .join("");
}

function renderProjects(rows) {
  if (!rows.length) {
    $("panel-projects").innerHTML =
      '<p class="empty">Keine Projekte. Zuerst „Demo laden“ oder „TED live“ ausführen.</p>';
    return;
  }
  $("panel-projects").innerHTML = `<table>
    <thead><tr><th>Datum</th><th>Kunde</th><th>Projekt</th><th>Firmen</th><th>Wert</th><th>Tags</th></tr></thead>
    <tbody>${rows
      .map((n) => {
        const firms = (n.companies || []).map((id) => LABELS[id] || id).join(", ");
        const title = n.source_url
          ? `<a href="${n.source_url}" target="_blank" rel="noreferrer">${n.title || n.id}</a>`
          : n.title || n.id;
        return `<tr>
          <td>${(n.published_at || "").slice(0, 10)}</td>
          <td>${n.buyer_name || "—"}</td>
          <td>${title}</td>
          <td>${firms}</td>
          <td>${fmtEur(n.value_eur)}</td>
          <td>${chips(n.tags)}</td>
        </tr>`;
      })
      .join("")}</tbody></table>`;
}

function renderCustomers(rows) {
  if (!rows.length) {
    $("panel-customers").innerHTML = '<p class="empty">Keine Kunden in der lokalen Datenbank.</p>';
    return;
  }
  $("panel-customers").innerHTML = `<table>
    <thead><tr><th>Kunde</th><th>Projekte</th><th>Wettbewerber</th><th>Wert (genannt)</th></tr></thead>
    <tbody>${rows
      .map(
        (c) => `<tr>
        <td>${c.name}</td>
        <td>${c.projects}</td>
        <td>${(c.companies || []).map((id) => LABELS[id] || id).join(", ")}</td>
        <td>${fmtEur(c.value_eur)}</td>
      </tr>`
      )
      .join("")}</tbody></table>`;
}

function renderPeople(rows) {
  if (!rows.length) {
    $("panel-people").innerHTML = `<p class="empty">
      Noch keine Personen. Sales-Navigator- oder Recruiter-CSV importieren
      (Spalten wie First Name, Last Name, Company, Title). LinkedIn nicht scrapen.
    </p>`;
    return;
  }
  $("panel-people").innerHTML = `<table>
    <thead><tr><th>Name</th><th>Firma</th><th>Rolle</th><th>Kunde</th><th>Projekt</th><th>Quelle</th></tr></thead>
    <tbody>${rows
      .map(
        (p) => `<tr>
        <td>${p.name}</td><td>${p.company}</td><td>${p.role}</td>
        <td>${p.customer}</td><td>${p.project}</td><td>${p.source}</td>
      </tr>`
      )
      .join("")}</tbody></table>`;
}

async function refresh() {
  const qs = companyQuery();
  const [stats, projects, customers, people] = await Promise.all([
    api("/api/stats"),
    api(`/api/projects${qs}`),
    api(`/api/customers${companySelect.value ? `?company=${companySelect.value}` : ""}`),
    api(`/api/people${companySelect.value ? `?company=${companySelect.value}` : ""}`),
  ]);
  renderKpis(stats);
  renderBars(stats);
  renderProjects(projects);
  renderCustomers(customers);
  renderPeople(people);
}

async function run(label, fn) {
  setStatus(`${label} …`);
  try {
    const result = await fn();
    setStatus(`${label}: ${JSON.stringify(result)}`);
    await refresh();
  } catch (err) {
    setStatus(`${label} fehlgeschlagen: ${err.message}`);
  }
}

document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    ["projects", "customers", "people", "sources"].forEach((id) => {
      $(`panel-${id}`).hidden = btn.dataset.tab !== id;
    });
  });
});

$("btn-demo").addEventListener("click", () =>
  run("Demo", () => api("/api/sync/demo", { method: "POST" }))
);
$("btn-ted").addEventListener("click", () =>
  run("TED", () => api("/api/sync/ted?limit=25", { method: "POST" }))
);
$("btn-vergabe").addEventListener("click", () =>
  run("Vergabe", () => api("/api/sync/vergabe?days=1", { method: "POST" }))
);

$("people-file").addEventListener("change", async (ev) => {
  const file = ev.target.files?.[0];
  if (!file) return;
  const body = new FormData();
  body.append("file", file);
  await run("Import", () => api("/api/import/people", { method: "POST", body }));
  ev.target.value = "";
});

[companySelect, focusSelect].forEach((el) => el.addEventListener("change", refresh));
searchInput.addEventListener("keydown", (ev) => {
  if (ev.key === "Enter") refresh();
});

(async function init() {
  const meta = await api("/api/meta");
  for (const c of meta.companies) {
    LABELS[c.id] = c.label;
    const opt = document.createElement("option");
    opt.value = c.id;
    opt.textContent = c.label;
    companySelect.append(opt);
  }
  await refresh();
})();
