const $ = (id) => document.getElementById(id);
const companySelect = $("company");
const searchInput = $("q");
const statusEl = $("status");
const LABELS = {};

function setStatus(text, show = true) {
  statusEl.hidden = !show;
  statusEl.textContent = text || "";
}

async function api(path, options) {
  const res = await fetch(path, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || data.error || res.statusText);
  return data;
}

function chips(items) {
  return (items || [])
    .map((t) => `<span class="chip${t === "in_scope" || t === "ai" || t === "data_platform" ? " focus" : ""}">${t}</span>`)
    .join("");
}

function qs() {
  const params = new URLSearchParams();
  if (companySelect.value) params.set("company", companySelect.value);
  if (searchInput.value.trim()) params.set("q", searchInput.value.trim());
  const s = params.toString();
  return s ? `?${s}` : "";
}

function renderKpis(stats) {
  $("kpis").innerHTML = [
    ["Personen im Fokus", stats.people],
    ["Posts (Fokus)", stats.posts],
    ["Kunden", stats.customers],
    ["Projekte", stats.projects],
  ]
    .map(([label, value]) => `<div class="kpi"><b>${value ?? 0}</b><span>${label}</span></div>`)
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

function empty(msg) {
  return `<p class="empty">${msg}</p>`;
}

function renderPosts(rows) {
  if (!rows.length) {
    $("panel-posts").innerHTML = empty(
      "Keine Posts. Demo laden, oder APIFY_TOKEN setzen und „Apify scrapen“."
    );
    return;
  }
  $("panel-posts").innerHTML = rows
    .map((p) => {
      const title = p.url
        ? `<a href="${p.url}" target="_blank" rel="noreferrer">${p.author || "Post"}</a>`
        : p.author;
      return `<article class="post">
        <header><strong>${title}</strong> · ${LABELS[p.company] || p.company} · ${(p.posted_at || "").slice(0, 10)}</header>
        <p>${(p.text || "").slice(0, 420)}</p>
        <div>${chips(p.customers)} ${chips(p.projects)} ${chips(p.tags.filter((t) => t === "ai" || t === "data_platform" || t === "in_scope"))}</div>
      </article>`;
    })
    .join("");
}

function renderPeople(rows) {
  if (!rows.length) {
    $("panel-people").innerHTML = empty("Keine Personen im Fokus.");
    return;
  }
  $("panel-people").innerHTML = `<table>
    <thead><tr><th>Name</th><th>Firma</th><th>Headline</th><th>Ort</th></tr></thead>
    <tbody>${rows
      .map((p) => {
        const name = p.profile_url
          ? `<a href="${p.profile_url}" target="_blank" rel="noreferrer">${p.name}</a>`
          : p.name;
        return `<tr><td>${name}</td><td>${LABELS[p.company] || p.company}</td><td>${p.headline}</td><td>${p.location}</td></tr>`;
      })
      .join("")}</tbody></table>`;
}

function renderCustomers(rows) {
  if (!rows.length) {
    $("panel-customers").innerHTML = empty("Noch keine Kunden aus Posts extrahiert.");
    return;
  }
  $("panel-customers").innerHTML = `<table>
    <thead><tr><th>Kunde</th><th>Erwähnungen</th><th>Firmen</th><th>Personen</th><th>Projekte</th></tr></thead>
    <tbody>${rows
      .map(
        (c) => `<tr>
        <td>${c.name}</td><td>${c.mentions}</td>
        <td>${(c.companies || []).map((id) => LABELS[id] || id).join(", ")}</td>
        <td>${(c.people || []).join(", ")}</td>
        <td>${(c.projects || []).join(", ")}</td>
      </tr>`
      )
      .join("")}</tbody></table>`;
}

function renderProjects(rows) {
  if (!rows.length) {
    $("panel-projects").innerHTML = empty("Noch keine Projektnamen in den Posts erkannt.");
    return;
  }
  $("panel-projects").innerHTML = `<table>
    <thead><tr><th>Projekt</th><th>Erwähnungen</th><th>Kunden</th><th>Firmen</th><th>Personen</th></tr></thead>
    <tbody>${rows
      .map(
        (p) => `<tr>
        <td>${p.name}</td><td>${p.mentions}</td>
        <td>${(p.customers || []).join(", ")}</td>
        <td>${(p.companies || []).map((id) => LABELS[id] || id).join(", ")}</td>
        <td>${(p.people || []).join(", ")}</td>
      </tr>`
      )
      .join("")}</tbody></table>`;
}

function renderCosts(data) {
  const a = data.assumptions;
  $("panel-costs").innerHTML = `
    <article class="prose">
      <h2>Günstigster Weg zu genau diesen Posts</h2>
      <p>Annahme: ${a.companies} Firmen, ${a.people} Köpfe in Data/AI Public Sector,
      ${a.posts_per_person} Posts/Person, alternativ ${a.post_search_hits} Treffer per Post-Suche.
      ${a.note}.</p>
    </article>
    <table>
      <thead><tr><th>Weg</th><th>Volumen</th><th>USD</th><th>EUR ca.</th><th>Wofür</th></tr></thead>
      <tbody>${data.providers
        .map(
          (p) => `<tr>
          <td>${p.label}</td><td>${p.volume}</td>
          <td>${p.usd}</td><td>${p.eur}</td><td>${p.best_for}</td>
        </tr>`
        )
        .join("")}</tbody>
    </table>
    <article class="prose">
      <p><strong>Empfehlung:</strong> ${data.cheapest.label} (~${data.cheapest.eur} € für einen Sweep).
      ${data.not_offered.diy_linkedin_login} ${data.not_offered.official_api}</p>
    </article>`;
}

async function refresh() {
  const query = qs();
  const [stats, posts, people, customers, projects, costs] = await Promise.all([
    api("/api/stats"),
    api(`/api/posts${query}`),
    api(`/api/people${companySelect.value ? `?company=${companySelect.value}` : ""}`),
    api(`/api/customers${companySelect.value ? `?company=${companySelect.value}` : ""}`),
    api(`/api/projects${companySelect.value ? `?company=${companySelect.value}` : ""}`),
    api("/api/costs"),
  ]);
  renderKpis(stats);
  renderBars(stats);
  renderPosts(posts);
  renderPeople(people);
  renderCustomers(customers);
  renderProjects(projects);
  renderCosts(costs);
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
    ["posts", "people", "customers", "projects", "costs"].forEach((id) => {
      $(`panel-${id}`).hidden = btn.dataset.tab !== id;
    });
  });
});

$("btn-demo").addEventListener("click", () =>
  run("Demo", () => api("/api/sync/demo", { method: "POST" }))
);
$("btn-apify").addEventListener("click", () =>
  run("Apify", () => api("/api/sync/apify?max_posts=40", { method: "POST" }))
);
$("btn-serper").addEventListener("click", () =>
  run("Serper", () => api("/api/sync/serper", { method: "POST" }))
);
companySelect.addEventListener("change", refresh);
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
