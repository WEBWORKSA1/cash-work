/* Remote jobs board: search and filter the auto-refreshed feed in data/jobs.json. */
(function () {
  "use strict";
  var list = document.getElementById("job-list");
  if (!list) return;
  var PER = 25;
  var all = [];
  var page = 1;
  var el = {
    q: document.getElementById("j-q"),
    cat: document.getElementById("j-cat"),
    src: document.getElementById("j-src"),
    type: document.getElementById("j-type"),
    sal: document.getElementById("j-sal"),
    count: document.getElementById("j-count"),
    pager: document.getElementById("j-pager")
  };
  function esc(s) { var d = document.createElement("div"); d.textContent = s == null ? "" : String(s); return d.innerHTML; }
  function fmt(iso) {
    var d = new Date(iso);
    return isNaN(d) ? "" : d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  }
  function options(select, values) {
    values.sort().forEach(function (v) {
      var o = document.createElement("option");
      o.value = v; o.textContent = v;
      select.appendChild(o);
    });
  }
  function filtered() {
    var q = el.q.value.trim().toLowerCase();
    return all.filter(function (j) {
      if (q && (j.title + " " + j.company + " " + (j.tags || []).join(" ") + " " + (j.location || "")).toLowerCase().indexOf(q) === -1) return false;
      if (el.cat.value && j.category !== el.cat.value) return false;
      if (el.src.value && j.source !== el.src.value) return false;
      if (el.type.value && (j.type || "").toLowerCase().indexOf(el.type.value) === -1) return false;
      if (el.sal.checked && !j.salary) return false;
      return true;
    });
  }
  function render() {
    var rows = filtered();
    var pages = Math.max(1, Math.ceil(rows.length / PER));
    page = Math.min(page, pages);
    el.count.textContent = rows.length.toLocaleString("en-US") + (rows.length === 1 ? " remote job" : " remote jobs");
    if (!rows.length) {
      list.innerHTML = '<li class="empty-state">No jobs match those filters. Clear the search or pick another category.</li>';
    } else {
      list.innerHTML = rows.slice((page - 1) * PER, page * PER).map(function (j) {
        var rel = j.source === "Remote OK" ? "noopener" : "nofollow noopener";
        return '<li class="job-row"><a class="job-title" href="' + esc(j.url) + '" rel="' + rel + '" target="_blank">' + esc(j.title) + "</a>" +
          '<span class="job-company">' + esc(j.company) + "</span>" +
          '<span class="job-meta">' + esc(j.location || "Remote") + (j.type ? " / " + esc(j.type) : "") + "</span>" +
          (j.salary ? '<span class="job-salary">' + esc(j.salary) + "</span>" : "") +
          '<span class="job-src">via ' + esc(j.source) + ", " + esc(fmt(j.date)) + "</span></li>";
      }).join("");
    }
    el.pager.innerHTML = pages > 1
      ? '<button class="btn btn-small btn-ghost" type="button" data-p="-1"' + (page === 1 ? " disabled" : "") + ">Previous</button>" +
        '<span class="small">Page ' + page + " of " + pages + "</span>" +
        '<button class="btn btn-small btn-ghost" type="button" data-p="1"' + (page === pages ? " disabled" : "") + ">Next</button>"
      : "";
  }
  el.pager.addEventListener("click", function (e) {
    var b = e.target.closest("[data-p]");
    if (!b) return;
    page += Number(b.getAttribute("data-p"));
    render();
    list.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  ["q", "cat", "src", "type", "sal"].forEach(function (k) {
    el[k].addEventListener(k === "q" ? "input" : "change", function () { page = 1; render(); });
  });
  var initial = new URLSearchParams(location.search).get("q");
  if (initial) el.q.value = initial;

  fetch((window.CashWork ? window.CashWork.root : "") + "data/jobs.json", { cache: "no-cache" })
    .then(function (r) { return r.json(); })
    .then(function (d) {
      all = d.jobs || [];
      if (!all.length) return;
      var cats = {}, srcs = {};
      all.forEach(function (j) { if (j.category) cats[j.category] = 1; if (j.source) srcs[j.source] = 1; });
      options(el.cat, Object.keys(cats));
      options(el.src, Object.keys(srcs));
      render();
    })
    .catch(function () { el.count.textContent = "Showing the latest saved jobs."; });
})();
