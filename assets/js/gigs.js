/* Gig directory: filter, sort and compare the prerendered ledger rows. */
(function () {
  "use strict";
  var list = document.getElementById("gig-ledger");
  if (!list) return;
  var rows = Array.prototype.slice.call(list.querySelectorAll(".ledger-row"));
  var f = {
    q: document.getElementById("g-q"),
    cat: document.getElementById("g-cat"),
    speed: document.getElementById("g-speed"),
    mode: document.getElementById("g-mode"),
    region: document.getElementById("g-region"),
    nocar: document.getElementById("g-nocar"),
    sort: document.getElementById("g-sort")
  };
  var count = document.getElementById("g-count");
  var SPEED_RANK = { instant: 0, fast: 1, weekly: 2, milestone: 3 };
  var gigData = {};
  var picked = [];

  var params = new URLSearchParams(location.search);
  ["q", "cat", "speed", "mode", "region"].forEach(function (k) {
    if (params.get(k) && f[k]) f[k].value = params.get(k);
  });

  function apply() {
    var q = (f.q.value || "").trim().toLowerCase();
    var shown = 0;
    rows.forEach(function (r) {
      var ok = true;
      if (q && r.textContent.toLowerCase().indexOf(q) === -1) ok = false;
      if (f.cat.value && r.dataset.cat !== f.cat.value) ok = false;
      if (f.speed.value && r.dataset.speed !== f.speed.value) ok = false;
      if (f.mode.value && r.dataset.mode !== f.mode.value) ok = false;
      if (f.region.value) {
        var regs = r.dataset.regions.split(" ");
        if (regs.indexOf(f.region.value) === -1 && regs.indexOf("Global") === -1) ok = false;
      }
      if (f.nocar.checked && r.dataset.car === "1") ok = false;
      r.hidden = !ok;
      if (ok) shown++;
    });
    var key = f.sort.value;
    var sorted = rows.slice().sort(function (a, b) {
      if (key === "pay") return Number(b.dataset.low) - Number(a.dataset.low);
      if (key === "name") return a.querySelector(".lr-name a").textContent.localeCompare(b.querySelector(".lr-name a").textContent);
      return (SPEED_RANK[a.dataset.speed] - SPEED_RANK[b.dataset.speed]) || (Number(b.dataset.low) - Number(a.dataset.low));
    });
    sorted.forEach(function (r) { list.appendChild(r); });
    count.textContent = shown === rows.length ? "Showing all " + rows.length + " platforms" : "Showing " + shown + " of " + rows.length + " platforms";
    var url = new URL(location.href);
    ["q", "cat", "speed", "mode", "region"].forEach(function (k) {
      if (f[k].value) url.searchParams.set(k, f[k].value); else url.searchParams.delete(k);
    });
    history.replaceState(null, "", url);
  }

  Object.keys(f).forEach(function (k) {
    f[k].addEventListener(k === "q" ? "input" : "change", apply);
  });
  document.getElementById("g-reset").addEventListener("click", function () {
    Object.keys(f).forEach(function (k) { if (k === "nocar") f[k].checked = false; else if (k !== "sort") f[k].value = ""; });
    apply();
  });

  // Speed chips mirror the speed select
  document.querySelectorAll("[data-speed-chip]").forEach(function (chip) {
    chip.addEventListener("click", function () {
      var v = chip.getAttribute("data-speed-chip");
      f.speed.value = f.speed.value === v ? "" : v;
      document.querySelectorAll("[data-speed-chip]").forEach(function (c) {
        c.setAttribute("aria-pressed", c.getAttribute("data-speed-chip") === f.speed.value ? "true" : "false");
      });
      apply();
    });
    chip.setAttribute("aria-pressed", chip.getAttribute("data-speed-chip") === f.speed.value ? "true" : "false");
  });

  // Compare up to three
  var bar = document.getElementById("compare-bar");
  var barText = document.getElementById("compare-text");
  rows.forEach(function (r) {
    var cell = document.createElement("div");
    cell.className = "lr-compare";
    var name = r.querySelector(".lr-name a").textContent;
    cell.innerHTML = '<label><input type="checkbox" aria-label="Compare ' + name.replace(/"/g, "") + '"></label>';
    r.appendChild(cell);
    cell.querySelector("input").addEventListener("change", function (e) {
      var id = r.dataset.id;
      if (e.target.checked) {
        if (picked.length >= 3) { e.target.checked = false; barText.textContent = "You can compare up to three at a time."; return; }
        picked.push(id);
      } else {
        picked = picked.filter(function (x) { return x !== id; });
      }
      bar.classList.toggle("show", picked.length > 0);
      barText.textContent = picked.length + " selected" + (picked.length < 2 ? ". Pick at least two." : ".");
    });
  });

  fetch((window.CashWork ? window.CashWork.root : "") + "data/gigs.json")
    .then(function (r) { return r.json(); })
    .then(function (d) { d.gigs.forEach(function (g) { gigData[g.id] = g; }); })
    .catch(function () {});

  var SPEED = { instant: "Instant cash-out", fast: "Within days", weekly: "Weekly", milestone: "After approval" };
  document.getElementById("compare-go").addEventListener("click", function () {
    if (picked.length < 2) { barText.textContent = "Pick at least two to compare."; return; }
    var gs = picked.map(function (id) { return gigData[id]; }).filter(Boolean);
    var esc = function (s) { var d = document.createElement("div"); d.textContent = s == null ? "" : String(s); return d.innerHTML; };
    var rowsDef = [
      ["Type of work", function (g) { return g.category_label; }],
      ["Typical pay", function (g) { return g.pay + " (" + g.pay_note + ")"; }],
      ["How fast you're paid", function (g) { return SPEED[g.speed]; }],
      ["Where", function (g) { return g.mode === "remote" ? "Remote" : "In person"; }],
      ["Regions", function (g) { return g.regions.join(", "); }],
      ["You'll need", function (g) { return g.needs.join(", "); }],
      ["Car required", function (g) { return g.car ? "Yes" : "No"; }],
      ["In short", function (g) { return g.summary; }]
    ];
    var html = '<div class="table-scroll"><table class="compare-table"><thead><tr><th scope="col">Compare</th>' +
      gs.map(function (g) { return '<th scope="col"><a href="' + esc(g.url) + '" rel="nofollow noopener" target="_blank">' + esc(g.name) + "</a></th>"; }).join("") +
      "</tr></thead><tbody>" +
      rowsDef.map(function (rd) { return '<tr><th scope="row">' + rd[0] + "</th>" + gs.map(function (g) { return "<td>" + esc(rd[1](g)) + "</td>"; }).join("") + "</tr>"; }).join("") +
      "</tbody></table></div>";
    var out = document.getElementById("compare-out");
    out.innerHTML = '<h2 id="compare-title">Side by side</h2>' + html;
    out.hidden = false;
    out.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  apply();
})();
