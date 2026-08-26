(function () {
  var DATA_URL = "alt-moves/series.json";
  var FILL = "#2ec4b6";
  var GREY_LINE = "#9aa4b2";
  var ZERO = "#6e7681";
  var TEXT = "#8b949e";
  var SHADE_IDS = null;

  var data = null;
  var on = {};
  var otherOn = true;

  function fetchJson() {
    if (window.ALT_MOVES_SERIES) return Promise.resolve(window.ALT_MOVES_SERIES);
    return fetch(DATA_URL, { cache: "no-store" }).then(function (r) {
      if (!r.ok) throw new Error("alt-moves " + r.status);
      return r.json();
    });
  }

  function shadeIds(d) {
    if (SHADE_IDS) return SHADE_IDS;
    var grey = {};
    (d.grey || []).forEach(function (id) { grey[id] = true; });
    SHADE_IDS = (d.order || []).filter(function (id) { return !grey[id]; });
    return SHADE_IDS;
  }

  function isOn(id) {
    if (on[id] === false) return false;
    if ((data.grey || []).indexOf(id) !== -1) return otherOn;
    return true;
  }

  function fitDpr(canvas, cssW, cssH) {
    var dpr = window.devicePixelRatio || 1;
    canvas.width = Math.max(1, Math.round(cssW * dpr));
    canvas.height = Math.max(1, Math.round(cssH * dpr));
    var ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return ctx;
  }

  function yRange(d, useOn) {
    var ids = Object.keys(d.coins);
    var lo = 0;
    var hi = 80;
    function consider(v) {
      if (v == null) return;
      if (v < lo) lo = v;
      if (v > hi) hi = v;
    }
    ids.forEach(function (id) {
      if (useOn && !isOn(id)) return;
      var arr = d.coins[id];
      for (var i = 0; i < arr.length; i++) consider(arr[i]);
    });
    if (useOn) {
      for (var i = 0; i < d.dates.length; i++) {
        var mn = null, mx = null;
        shadeIds(d).forEach(function (id) {
          if (!isOn(id)) return;
          var v = d.coins[id][i];
          if (v == null) return;
          if (mn == null || v < mn) mn = v;
          if (mx == null || v > mx) mx = v;
        });
        consider(mn); consider(mx);
      }
    } else {
      for (var j = 0; j < d.shadeMin.length; j++) {
        consider(d.shadeMin[j]);
        consider(d.shadeMax[j]);
      }
    }
    var bot = (hi - lo) * 0.04;
    if (bot < 8) bot = 8;
    if (lo > 0) lo = 0;
    return { lo: lo - bot, hi: hi };
  }

  function dayShade(d, i, useOn) {
    if (!useOn) return { min: d.shadeMin[i], max: d.shadeMax[i] };
    var mn = null, mx = null;
    shadeIds(d).forEach(function (id) {
      if (!isOn(id)) return;
      var v = d.coins[id][i];
      if (v == null) return;
      if (mn == null || v < mn) mn = v;
      if (mx == null || v > mx) mx = v;
    });
    return { min: mn, max: mx };
  }

  function drawChart(canvas, d, opts) {
    opts = opts || {};
    var thumb = !!opts.thumb;
    var useOn = !thumb;
    var rect = canvas.getBoundingClientRect();
    var w = rect.width || canvas.clientWidth || 320;
    var h = rect.height || canvas.clientHeight || 140;
    var ctx = fitDpr(canvas, w, h);
    ctx.clearRect(0, 0, w, h);

    var padL = thumb ? 2 : 44;
    var padR = thumb ? 2 : 10;
    var padT = thumb ? 2 : 4;
    var padB = thumb ? 4 : 22;
    var n = d.dates.length;
    var yr = yRange(d, useOn);
    function X(i) { return padL + (i / (n - 1)) * (w - padL - padR); }
    function Y(v) { return padT + (1 - (v - yr.lo) / (yr.hi - yr.lo)) * (h - padT - padB); }

    if (!thumb) {
      ctx.strokeStyle = "rgba(28,37,48,0.9)";
      ctx.lineWidth = 1;
      var ticks = 5;
      ctx.font = "11px ui-sans-serif, system-ui, sans-serif";
      ctx.fillStyle = TEXT;
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";
      for (var t = 0; t <= ticks; t++) {
        var v = yr.lo + (yr.hi - yr.lo) * (t / ticks);
        var y = Y(v);
        ctx.beginPath();
        ctx.moveTo(padL, y);
        ctx.lineTo(w - padR, y);
        ctx.stroke();
        ctx.fillText(Math.round(v) + "%", padL - 6, y);
      }
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      var lastM = "";
      for (var i = 0; i < n; i++) {
        var m = d.dates[i].slice(0, 7);
        if (m === lastM) continue;
        if (d.dates[i].slice(8) !== "01" && i !== 0) continue;
        lastM = m;
        var label = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][parseInt(d.dates[i].slice(5, 7), 10) - 1];
        if (label) ctx.fillText(label, X(i), h - padB + 6);
      }
    }

    var colA = (d.strokes && d.strokes.colour) != null ? d.strokes.colour : 0.4;
    var greyA = (d.strokes && d.strokes.grey) != null ? d.strokes.grey : 0.3;
    var floorA = (d.strokes && d.strokes.floor) != null ? d.strokes.floor : 0.4;
    if (!thumb) { colA = 0.92; greyA = 0.22; floorA = 0.95; }

    function strokeSeries(arr, color, alpha, lw) {
      ctx.strokeStyle = color;
      ctx.globalAlpha = alpha;
      ctx.lineWidth = lw;
      ctx.lineJoin = "round";
      ctx.lineCap = "round";
      ctx.beginPath();
      var started = false;
      for (var i = 0; i < arr.length; i++) {
        var v = arr[i];
        if (v == null) { started = false; continue; }
        if (!started) { ctx.moveTo(X(i), Y(v)); started = true; }
        else ctx.lineTo(X(i), Y(v));
      }
      ctx.stroke();
      ctx.globalAlpha = 1;
    }

    (d.grey || []).forEach(function (id) {
      if (useOn && !isOn(id)) return;
      strokeSeries(d.coins[id], GREY_LINE, greyA, thumb ? 0.7 : 0.85);
    });

    (d.order || []).forEach(function (id) {
      if (useOn && !isOn(id)) return;
      var color = (d.colors && d.colors[id]) || GREY_LINE;
      strokeSeries(d.coins[id], color, colA, thumb ? 0.8 : 0.95);
    });

    ctx.beginPath();
    var startedHi = false;
    for (var i = 0; i < n; i++) {
      var s = dayShade(d, i, useOn);
      if (s.max == null) { startedHi = false; continue; }
      if (!startedHi) { ctx.moveTo(X(i), Y(s.max)); startedHi = true; }
      else ctx.lineTo(X(i), Y(s.max));
    }
    for (var i = n - 1; i >= 0; i--) {
      var s2 = dayShade(d, i, useOn);
      if (s2.min == null) continue;
      ctx.lineTo(X(i), Y(s2.min));
    }
    ctx.closePath();
    ctx.globalAlpha = thumb ? 0.22 : 0.28;
    ctx.fillStyle = FILL;
    ctx.fill();
    ctx.globalAlpha = 1;

    var floor = [];
    var ceil = [];
    for (var i = 0; i < n; i++) {
      var s3 = dayShade(d, i, useOn);
      floor.push(s3.min);
      ceil.push(s3.max);
    }
    strokeSeries(ceil, FILL, thumb ? 0.35 : 0.55, 0.85);
    strokeSeries(floor, FILL, floorA, thumb ? 1.05 : 1.25);

    ctx.globalAlpha = 0.85;
    ctx.strokeStyle = ZERO;
    ctx.lineWidth = 0.9;
    ctx.beginPath();
    ctx.moveTo(padL, Y(0));
    ctx.lineTo(w - padR, Y(0));
    ctx.stroke();
    ctx.globalAlpha = 1;
  }

  function buildKey(el, d) {
    el.innerHTML = "";
    (d.order || []).forEach(function (id) {
      var b = document.createElement("button");
      b.type = "button";
      b.dataset.id = id;
      if (on[id] === false) b.classList.add("is-off");
      var sw = document.createElement("span");
      sw.className = "alt-moves-swatch";
      sw.style.background = (d.colors && d.colors[id]) || GREY_LINE;
      b.appendChild(sw);
      b.appendChild(document.createTextNode(id));
      b.addEventListener("click", function () {
        on[id] = on[id] === false ? true : false;
        b.classList.toggle("is-off", on[id] === false);
        redrawFull();
      });
      el.appendChild(b);
    });
    var other = document.createElement("button");
    other.type = "button";
    other.className = otherOn ? "" : "is-off";
    var sw2 = document.createElement("span");
    sw2.className = "alt-moves-swatch";
    sw2.style.background = GREY_LINE;
    other.appendChild(sw2);
    other.appendChild(document.createTextNode("Other Coins"));
    other.addEventListener("click", function () {
      otherOn = !otherOn;
      other.classList.toggle("is-off", !otherOn);
      redrawFull();
    });
    el.appendChild(other);
  }

  function redrawThumb() {
    var c = document.getElementById("altMovesThumb");
    if (c && data) drawChart(c, data, { thumb: true });
  }
  function redrawFull() {
    var c = document.getElementById("altMovesFull");
    if (c && data) drawChart(c, data, { thumb: false });
  }

  function openModal() {
    var root = document.getElementById("altMovesModal");
    if (!root) return;
    root.hidden = false;
    requestAnimationFrame(function () {
      redrawFull();
    });
  }
  function closeModal() {
    var root = document.getElementById("altMovesModal");
    if (root) root.hidden = true;
  }

  function bind() {
    var card = document.getElementById("altMovesCard");
    if (card) {
      card.addEventListener("click", openModal);
      card.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openModal(); }
      });
    }
    document.addEventListener("click", function (e) {
      if (e.target.closest("[data-alt-moves-close]")) closeModal();
    });
    document.addEventListener("keydown", function (e) {
      var root = document.getElementById("altMovesModal");
      if (e.key === "Escape" && root && !root.hidden) closeModal();
    });
    window.addEventListener("resize", function () {
      redrawThumb();
      var root = document.getElementById("altMovesModal");
      if (root && !root.hidden) redrawFull();
    });
  }

  fetchJson().then(function (d) {
    data = d;
    (d.order || []).forEach(function (id) { on[id] = true; });
    bind();
    var key = document.getElementById("altMovesKey");
    if (key) buildKey(key, d);
    redrawThumb();
  }).catch(function (err) {
    console.warn(err);
  });
})();
