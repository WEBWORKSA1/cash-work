/* Home page payday cheque: turns a kind of work and a number of hours into a filled-in cheque. */
(function () {
  "use strict";
  var form = document.getElementById("cheque-form");
  if (!form) return;

  var WORK = {
    delivery: { label: "food delivery", rate: 18, speed: "Instant cash-out" },
    rideshare: { label: "rideshare driving", rate: 22, speed: "Instant cash-out" },
    shopping: { label: "grocery shopping", rate: 18, speed: "Instant cash-out" },
    shifts: { label: "warehouse and event shifts", rate: 18, speed: "Paid within days" },
    tasks: { label: "home tasks and handyman work", rate: 32, speed: "Paid within days" },
    pets: { label: "dog walking and pet sitting", rate: 20, speed: "Paid within days" },
    tutoring: { label: "online tutoring", rate: 25, speed: "Paid weekly" },
    ai: { label: "AI training work", rate: 25, speed: "Paid weekly" },
    research: { label: "paid research studies", rate: 30, speed: "Paid after approval" },
    freelance: { label: "freelance projects", rate: 35, speed: "Paid on approval" }
  };

  var ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
    "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"];
  var tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"];
  function under1000(n) {
    var out = [];
    if (n >= 100) { out.push(ones[Math.floor(n / 100)] + " hundred"); n %= 100; }
    if (n >= 20) { out.push(tens[Math.floor(n / 10)] + (n % 10 ? "-" + ones[n % 10] : "")); }
    else if (n > 0) { out.push(ones[n]); }
    return out.join(" ");
  }
  function words(n) {
    if (n === 0) return "Zero";
    var parts = [];
    if (n >= 1000) { parts.push(under1000(Math.floor(n / 1000)) + " thousand"); n %= 1000; }
    if (n > 0) parts.push(under1000(n));
    var s = parts.join(" ");
    return s.charAt(0).toUpperCase() + s.slice(1);
  }

  var $ = function (id) { return document.getElementById(id); };
  var stamp = $("cq-stamp");
  var timer;

  function update(animate) {
    var w = WORK[form.work.value] || WORK.delivery;
    var hours = Number(form.hours.value);
    var amount = Math.round(w.rate * hours);
    $("cq-hours-out").textContent = hours + " hr";
    $("cq-figure").textContent = "$" + amount.toLocaleString("en-US");
    $("cq-words").textContent = words(amount) + " dollars";
    $("cq-for").textContent = hours + " hours of " + w.label + " at about $" + w.rate + "/hr";
    $("cq-speed").textContent = w.speed;
    if (animate && stamp) {
      clearTimeout(timer);
      timer = setTimeout(function () {
        stamp.classList.remove("thump");
        void stamp.offsetWidth;
        stamp.classList.add("thump");
      }, 220);
    }
  }

  var d = new Date();
  $("cq-date").textContent = d.toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" });
  $("cq-no").textContent = "No. " + String(d.getMonth() + 1).padStart(2, "0") + String(d.getDate()).padStart(2, "0") + "-" + d.getFullYear();

  form.addEventListener("input", function () { update(true); });
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    location.href = (window.CashWork ? window.CashWork.root : "") + "gigs.html?cat=" + encodeURIComponent(form.work.value);
  });
  update(false);
})();
