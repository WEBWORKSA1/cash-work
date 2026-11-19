/* Get matched: a six-question quiz that ranks the gig directory for one person,
   shows the top three straight away and unlocks the full plan with an email. */
(function () {
  "use strict";
  var quiz = document.getElementById("match-quiz");
  if (!quiz) return;
  var steps = Array.prototype.slice.call(quiz.querySelectorAll(".q"));
  var bars = document.getElementById("match-progress");
  var results = document.getElementById("match-results");
  var gigs = [];
  var current = 0;
  var top = [];

  bars.innerHTML = steps.map(function () { return "<span></span>"; }).join("");
  function show(i, focus) {
    steps.forEach(function (s, n) { s.classList.toggle("active", n === i); });
    Array.prototype.forEach.call(bars.children, function (b, n) { b.classList.toggle("done", n <= i); });
    current = i;
    var h = steps[i].querySelector("h3");
    if (h && focus) { h.setAttribute("tabindex", "-1"); h.focus({ preventScroll: true }); }
  }
  function answers() {
    var fd = new FormData(quiz);
    return {
      when: fd.get("when"), where: fd.get("where"), vehicle: fd.get("vehicle"),
      skills: fd.getAll("skills"), region: fd.get("region"),
      hours: Number(fd.get("hours") || 10), goal: Number(fd.get("goal") || 500)
    };
  }
  function answered(step) {
    var inputs = step.querySelectorAll("input[type=radio], input[type=checkbox]");
    if (!inputs.length) return true;
    return Array.prototype.some.call(inputs, function (i) { return i.checked; });
  }

  quiz.addEventListener("click", function (e) {
    var next = e.target.closest("[data-next]");
    var back = e.target.closest("[data-back]");
    var msg = steps[current].querySelector(".q-msg");
    if (next) {
      e.preventDefault();
      if (!answered(steps[current])) { if (msg) msg.textContent = "Pick at least one option to continue."; return; }
      if (msg) msg.textContent = "";
      if (current < steps.length - 1) show(current + 1, true); else finish();
    }
    if (back) { e.preventDefault(); if (current > 0) show(current - 1, true); }
  });
  var hoursIn = quiz.querySelector('input[name="hours"]');
  if (hoursIn) hoursIn.addEventListener("input", function () { document.getElementById("hours-out").textContent = hoursIn.value + " hours"; });

  var SKILL = {
    driving: ["delivery", "rideshare", "shopping"],
    physical: ["shifts", "tasks"],
    people: ["pets", "care"],
    pro: ["freelance", "ai"],
    teaching: ["tutoring"],
    opinions: ["research", "micro"],
    assets: ["selling", "rental"]
  };
  var RATE = { delivery: 18, rideshare: 22, shopping: 18, shifts: 18, tasks: 30, pets: 20, care: 20, freelance: 35, ai: 25, tutoring: 25, research: 30, micro: 5, selling: 15, rental: 15 };
  var SPEED = { instant: "Instant cash-out", fast: "Paid within days", weekly: "Paid weekly", milestone: "Paid after approval" };

  function score(g, a) {
    if (a.vehicle !== "car" && g.car) return -99;
    if (a.vehicle === "none" && ["delivery", "rideshare", "shopping"].indexOf(g.category) !== -1) return -99;
    if (a.region && a.region !== "Other" && g.regions.indexOf(a.region) === -1 && g.regions.indexOf("Global") === -1) return -99;
    if (a.region === "Other" && g.regions.indexOf("Global") === -1) return -99;
    var s = 0;
    var sp = { today: { instant: 6, fast: 2, weekly: -1, milestone: -4 }, month: { instant: 3, fast: 3, weekly: 1, milestone: -1 }, wait: { instant: 1, fast: 1, weekly: 1, milestone: 2 } };
    s += (sp[a.when] || sp.month)[g.speed] || 0;
    if (a.where === "home" && g.mode === "local") s -= 6;
    if (a.where === "out" && g.mode === "remote") s -= 3;
    var wanted = [];
    a.skills.forEach(function (k) { wanted = wanted.concat(SKILL[k] || []); });
    if (wanted.indexOf(g.category) !== -1) s += 6; else s -= 2;
    if (g.category === "micro" && a.skills.indexOf("opinions") === -1) s -= 3;
    s += Math.min(6, (g.pay_low || 0) / 8);
    return s;
  }

  function esc(s) { var d = document.createElement("div"); d.textContent = s == null ? "" : String(s); return d.innerHTML; }

  function finish() {
    var a = answers();
    top = gigs.map(function (g) { return { g: g, s: score(g, a) }; })
      .filter(function (x) { return x.s > -50; })
      .sort(function (x, y) { return y.s - x.s; })
      .slice(0, 10).map(function (x) { return x.g; });
    var avg = top.length ? top.slice(0, 3).reduce(function (t, g) { return t + (RATE[g.category] || 15); }, 0) / Math.min(3, top.length) : 15;
    var monthly = Math.round(avg * a.hours * 4.33);
    quiz.hidden = true;
    results.hidden = false;
    document.getElementById("match-summary").textContent = top.length
      ? "At " + a.hours + " hours a week, your top matches typically gross about $" + monthly.toLocaleString("en-US") + " a month" +
        (a.goal ? (monthly >= a.goal ? ", which covers your $" + a.goal.toLocaleString("en-US") + " goal." : ". To reach $" + a.goal.toLocaleString("en-US") + ", plan for about " + Math.ceil(a.goal / (avg * 4.33)) + " hours a week.") : ".")
      : "Nothing in the directory fits every answer. Try widening where you can work or the region.";
    document.getElementById("match-list").innerHTML = top.map(function (g, i) {
      return '<li class="' + (i >= 3 ? "locked" : "") + '"' + (i >= 3 ? ' aria-hidden="true"' : "") + "><div><strong>" + esc(g.name) + "</strong><br><span class=\"small muted\">" +
        esc(g.category_label) + ". " + esc(g.summary) + "</span></div><div><span class=\"speed speed-" + g.speed + "\">" + SPEED[g.speed] + "</span><br><span class=\"small\">" + esc(g.pay) + "</span></div></li>";
    }).join("");
    var hidden = Math.max(0, top.length - 3);
    document.getElementById("unlock-count").textContent = hidden ? hidden + " more matches and your 7-day plan" : "your 7-day plan";
    var lead = document.getElementById("match-lead");
    lead.querySelector('input[name="quiz_answers"]').value = JSON.stringify(a);
    lead.querySelector('input[name="top_matches"]').value = top.map(function (g) { return g.name; }).join(", ");
    var rh = results.querySelector("h2"); rh.setAttribute("tabindex", "-1"); rh.focus();
  }

  function plan(a) {
    var first = top[0], second = top[1], third = top[2];
    var p = [];
    if (first) p.push("Day 1: Apply to " + first.name + " and " + (second ? second.name : "one backup") + " tonight. Approval can take days, so apply to two at once.");
    p.push("Day 2: Work out your true hourly pay with the gig pay calculator, so you know which offers to decline.");
    if (third) p.push("Day 3: Add " + third.name + " as a backup for slow days.");
    p.push("Day 4: Block " + a.hours + " hours in your calendar for the week, starting with the busiest times for your type of work.");
    p.push("Day 5: Open a separate savings pot and move " + (a.when === "today" ? "15%" : "20–25%") + " of every payout into it for taxes.");
    p.push("Day 6: Track every hour and payout. Drop anything that nets under your minimum.");
    p.push("Day 7: Review the week, keep the best one or two apps, and come back here for new fast-pay listings.");
    return p;
  }

  document.getElementById("match-lead").addEventListener("cw:sent", function () {
    document.querySelectorAll("#match-list li.locked").forEach(function (li) { li.classList.remove("locked"); li.removeAttribute("aria-hidden"); });
    var a = answers();
    var box = document.getElementById("match-plan");
    box.innerHTML = "<h3>Your 7-day plan</h3><ol>" + plan(a).map(function (s) { return "<li>" + esc(s) + "</li>"; }).join("") +
      '</ol><p><button class="btn btn-ghost btn-small" type="button" onclick="window.print()">Print or save as PDF</button></p>';
    box.hidden = false;
    document.getElementById("unlock-box").hidden = true;
    box.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  document.getElementById("match-restart").addEventListener("click", function () {
    results.hidden = true; quiz.hidden = false; show(0, true);
  });

  fetch((window.CashWork ? window.CashWork.root : "") + "data/gigs.json")
    .then(function (r) { return r.json(); })
    .then(function (d) { gigs = d.gigs || []; })
    .catch(function () {});
  show(0);
})();
