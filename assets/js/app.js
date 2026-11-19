/* Cash.Work shared behaviour: navigation, cookie notice, private form delivery,
   donations and click-to-load videos. No dependencies. */
(function () {
  "use strict";

  // The inbox address is never written in the page source; it is assembled only when needed.
  var _c = [120, 122, 110, 57, 119, 116, 108, 120, 114, 75, 60, 108, 126, 118, 125, 122, 130, 109, 112, 130];
  function inbox() { return _c.map(function (n) { return String.fromCharCode(n - 11); }).reverse().join(""); }

  var root = (function () {
    var s = document.querySelector('script[src*="assets/js/app.js"]');
    return s ? s.getAttribute("src").split("assets/js/app.js")[0] : "";
  })();
  window.CashWork = { root: root };

  // Mobile navigation
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.textContent = open ? "Close" : "Menu";
    });
  }

  // Cookie notice (informational; Google's consent message handles ad consent where required)
  var cookie = document.getElementById("cookie");
  try {
    if (cookie && !localStorage.getItem("cw-cookie-ok")) cookie.hidden = false;
  } catch (e) { if (cookie) cookie.hidden = false; }
  document.addEventListener("click", function (e) {
    if (e.target.closest("[data-cookie-ok]")) {
      try { localStorage.setItem("cw-cookie-ok", "1"); } catch (err) {}
      cookie.hidden = true;
    }
  });

  // Forms: every form with data-form is delivered privately to the site inbox.
  function serialize(form) {
    var data = {};
    new FormData(form).forEach(function (v, k) {
      if (data[k]) data[k] = data[k] + ", " + v; else data[k] = v;
    });
    return data;
  }

  function send(payload, subject) {
    payload._subject = subject;
    payload._template = "table";
    payload._captcha = "false";
    payload.page = location.href;
    payload.submitted_at = new Date().toISOString();
    return fetch("https://formsubmit.co/ajax/" + inbox(), {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(payload)
    }).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    });
  }
  window.CashWork.send = send;

  document.querySelectorAll("form[data-form]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var status = form.querySelector(".form-status");
      var btn = form.querySelector('button[type="submit"]');
      var data = serialize(form);
      if (data._honey) return; // bot trap
      delete data._honey;
      if (!form.checkValidity()) { form.reportValidity(); return; }
      var label = btn ? btn.textContent : "";
      if (btn) { btn.disabled = true; btn.textContent = "Sending…"; }
      if (status) { status.className = "form-status"; status.textContent = ""; }
      data.form = form.getAttribute("data-form");
      send(data, form.getAttribute("data-subject") || "Cash.Work: new " + data.form + " submission")
        .then(function () {
          if (status) { status.className = "form-status ok"; status.textContent = form.getAttribute("data-success") || "Sent. We reply within two business days."; }
          form.reset();
          form.dispatchEvent(new CustomEvent("cw:sent", { detail: data }));
        })
        .catch(function () {
          if (status) { status.className = "form-status err"; status.textContent = "Not sent. Check your connection and press the button again."; }
        })
        .finally(function () { if (btn) { btn.disabled = false; btn.textContent = label; } });
    });
  });

  // Donations through PayPal, with the account built at click time.
  function donate(amount, freq) {
    var p = new URLSearchParams({
      business: inbox(),
      item_name: "Support Cash.Work operations",
      currency_code: "USD",
      no_recurring: freq === "monthly" ? "0" : "1"
    });
    if (amount) p.set("amount", amount);
    window.open("https://www.paypal.com/donate/?" + p.toString(), "_blank", "noopener");
  }
  document.addEventListener("click", function (e) {
    var b = e.target.closest("[data-donate]");
    if (!b) return;
    e.preventDefault();
    var amt = b.getAttribute("data-donate");
    if (amt === "custom") {
      var input = document.getElementById("donate-custom");
      amt = input && input.value ? String(Math.max(1, Math.round(Number(input.value)))) : "";
    }
    var freq = (document.querySelector('input[name="donate-freq"]:checked') || {}).value;
    donate(amt, freq);
  });

  // Click-to-load YouTube (privacy-enhanced mode, nothing loads until the visitor asks)
  document.addEventListener("click", function (e) {
    var b = e.target.closest(".video-play");
    if (!b) return;
    var id = b.getAttribute("data-video");
    if (!/^[\w-]{6,20}$/.test(id)) return;
    var f = document.createElement("iframe");
    f.src = "https://www.youtube-nocookie.com/embed/" + id + "?autoplay=1&rel=0";
    f.title = b.getAttribute("aria-label") || "Video";
    f.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
    f.allowFullscreen = true;
    b.replaceWith(f);
  });

  // Share buttons
  document.addEventListener("click", function (e) {
    var s = e.target.closest("[data-share]");
    if (!s) return;
    e.preventDefault();
    var data = { title: document.title, url: location.href };
    if (navigator.share) { navigator.share(data).catch(function () {}); }
    else if (navigator.clipboard) {
      navigator.clipboard.writeText(location.href).then(function () { s.textContent = "Link copied"; });
    }
  });
})();
