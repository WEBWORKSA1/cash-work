/* Cash.Work calculators. Each runs only if its form is on the page. All math happens in the browser. */
(function () {
  "use strict";
  var money = function (n, d) {
    if (!isFinite(n)) return "—";
    return (n < 0 ? "-$" : "$") + Math.abs(n).toLocaleString("en-US", { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 });
  };
  var num = function (form, name) { var v = parseFloat(form[name].value); return isFinite(v) ? v : 0; };
  var rows = function (pairs) {
    return pairs.map(function (p) { return "<tr><td>" + p[0] + "</td><td>" + p[1] + "</td></tr>"; }).join("");
  };
  function bind(id, fn) {
    var form = document.getElementById(id);
    if (!form) return;
    var run = function (e) { if (e) e.preventDefault(); fn(form); };
    form.addEventListener("input", run);
    form.addEventListener("submit", run);
    run();
  }

  // 1. Gig pay: what an hour of app work really pays
  bind("t-gig", function (f) {
    var gross = num(f, "gross"), tips = num(f, "tips"), hours = num(f, "hours"), dist = num(f, "distance"),
        cpm = num(f, "cost"), other = num(f, "other"), tax = num(f, "tax") / 100;
    var vehicle = dist * cpm;
    var beforeTax = gross + tips - vehicle - other;
    var taxes = Math.max(0, beforeTax) * tax;
    var net = beforeTax - taxes;
    var hourlyGross = hours ? (gross + tips) / hours : 0;
    var hourlyNet = hours ? net / hours : 0;
    document.getElementById("gig-big").textContent = money(hourlyNet, 2) + " an hour";
    document.getElementById("gig-sub").textContent = hours
      ? "The app shows " + money(hourlyGross, 2) + "/hr. After vehicle costs, other costs and a tax set-aside you keep " + money(hourlyNet, 2) + "/hr."
      : "Enter the hours you were logged in, including waiting time.";
    document.getElementById("gig-table").innerHTML = rows([
      ["Earnings plus tips", money(gross + tips, 2)],
      ["Vehicle cost (" + dist + " × " + money(cpm, 2) + ")", "−" + money(vehicle, 2)],
      ["Other costs", "−" + money(other, 2)],
      ["Tax set-aside (" + Math.round(tax * 100) + "%)", "−" + money(taxes, 2)],
      ["You keep", money(net, 2)],
      ["Share of gross you keep", (gross + tips) ? Math.round(net / (gross + tips) * 100) + "%" : "—"]
    ]);
  });

  // 2. Hourly to salary (and back)
  bind("t-salary", function (f) {
    var mode = f.mode.value, hpw = num(f, "hpw"), weeks = num(f, "weeks");
    var hourly, annual;
    if (mode === "toHourly") { annual = num(f, "amount"); hourly = hpw && weeks ? annual / (hpw * weeks) : 0; }
    else { hourly = num(f, "amount"); annual = hourly * hpw * weeks; }
    document.getElementById("sal-label").textContent = mode === "toHourly" ? "Annual salary ($)" : "Hourly rate ($)";
    document.getElementById("sal-big").textContent = mode === "toHourly" ? money(hourly, 2) + " an hour" : money(annual) + " a year";
    document.getElementById("sal-table").innerHTML = rows([
      ["Hourly", money(hourly, 2)],
      ["Daily (" + (hpw / 5).toFixed(1) + " hrs)", money(hourly * hpw / 5, 2)],
      ["Weekly", money(hourly * hpw, 2)],
      ["Every two weeks", money(hourly * hpw * 2, 2)],
      ["Monthly (average)", money(annual / 12, 2)],
      ["Yearly (" + weeks + " paid weeks)", money(annual)]
    ]);
  });

  // 3. Freelance rate: the minimum rate that funds the life you want
  bind("t-rate", function (f) {
    var takeHome = num(f, "income"), costs = num(f, "costs"), tax = num(f, "tax") / 100,
        weeksOff = num(f, "off"), billable = num(f, "billable"), buffer = num(f, "buffer") / 100;
    var needed = (takeHome / Math.max(0.01, 1 - tax)) + costs;
    var hours = Math.max(0, 52 - weeksOff) * billable;
    var rate = hours ? needed / hours * (1 + buffer) : 0;
    document.getElementById("rate-big").textContent = money(Math.ceil(rate)) + " an hour";
    document.getElementById("rate-sub").textContent = hours
      ? "Charge at least this to take home " + money(takeHome) + " after taxes and costs, billing " + hours.toLocaleString() + " hours a year."
      : "Add billable hours to see your rate.";
    document.getElementById("rate-table").innerHTML = rows([
      ["Revenue you need", money(needed)],
      ["Billable hours per year", hours.toLocaleString()],
      ["Half-day rate (4 hrs)", money(Math.ceil(rate) * 4)],
      ["Day rate (8 hrs)", money(Math.ceil(rate) * 8)],
      ["Price for a 10-hour project", money(Math.ceil(rate) * 10)],
      ["Monthly retainer (20 hrs)", money(Math.ceil(rate) * 20)]
    ]);
  });

  // 4. Cash goal planner
  bind("t-goal", function (f) {
    var goal = num(f, "goal"), saved = num(f, "saved"), rate = num(f, "rate");
    var deadline = f.deadline.value ? new Date(f.deadline.value + "T23:59:59") : null;
    var gap = Math.max(0, goal - saved);
    var days = deadline ? Math.max(1, Math.ceil((deadline - new Date()) / 86400000)) : 30;
    var weeks = Math.max(1, days / 7);
    var hoursTotal = rate ? gap / rate : 0;
    var perWeek = hoursTotal / weeks;
    document.getElementById("goal-big").textContent = gap ? perWeek.toFixed(1) + " hours a week" : "Goal reached";
    var speedTip = days <= 7 ? "With a week or less, stick to instant cash-out work: delivery, rideshare and local cash jobs."
      : days <= 30 ? "Within a month, mix instant cash-out apps with shift apps that pay within days."
      : "With more than a month, you can add higher-paying work that pays on approval, like freelancing and research studies.";
    document.getElementById("goal-sub").textContent = speedTip;
    document.getElementById("goal-table").innerHTML = rows([
      ["Still to earn", money(gap)],
      ["Days left", String(days)],
      ["Total hours at " + money(rate) + "/hr", hoursTotal.toFixed(1)],
      ["Hours per day", (hoursTotal / days).toFixed(1)],
      ["Earn per week", money(gap / weeks)]
    ]);
    var link = document.getElementById("goal-link");
    if (link) link.href = link.getAttribute("data-base") + (days <= 7 ? "?speed=instant" : days <= 30 ? "?speed=fast" : "");
  });

  // 5. Job scam checker
  bind("t-scam", function (f) {
    var boxes = f.querySelectorAll('input[type="checkbox"]');
    var score = 0, max = 0, hits = [];
    boxes.forEach(function (b) {
      var w = Number(b.getAttribute("data-w"));
      max += w;
      if (b.checked) { score += w; hits.push(b.getAttribute("data-tip")); }
    });
    var pct = max ? Math.round(score / max * 100) : 0;
    var meter = document.getElementById("scam-meter");
    meter.className = "meter" + (score >= 6 ? " bad" : score >= 3 ? " warn" : "");
    meter.firstElementChild.style.width = Math.min(100, pct * 2) + "%";
    var verdict = score >= 6 ? "High risk. Do not send money, documents or bank details."
      : score >= 3 ? "Warning signs. Verify the company independently before going further."
      : score > 0 ? "Low risk so far, but keep checking."
      : "Tick anything that applies to the offer.";
    document.getElementById("scam-big").textContent = verdict;
    document.getElementById("scam-tips").innerHTML = hits.length
      ? hits.map(function (t) { return "<li>" + t + "</li>"; }).join("")
      : "<li>Look up the company's own careers page and apply there, not through a chat link.</li>";
  });
})();
