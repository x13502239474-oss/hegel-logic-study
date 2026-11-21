/* 黑格尔逻辑学研究室 — 交互层（无依赖） */
(function () {
  "use strict";

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ---------- 移动端抽屉 ---------- */
  var drawer = $("#drawer");
  var openBtn = $("#menuBtn");
  var closeBtn = $("#drawerClose");

  function openDrawer() {
    if (!drawer) return;
    drawer.classList.add("is-open");
    document.body.style.overflow = "hidden";
    if (openBtn) openBtn.setAttribute("aria-expanded", "true");
  }
  function closeDrawer() {
    if (!drawer) return;
    drawer.classList.remove("is-open");
    document.body.style.overflow = "";
    if (openBtn) openBtn.setAttribute("aria-expanded", "false");
  }
  if (openBtn) openBtn.addEventListener("click", openDrawer);
  if (closeBtn) closeBtn.addEventListener("click", closeDrawer);
  if (drawer) {
    drawer.addEventListener("click", function (e) {
      if (e.target === drawer) closeDrawer();
    });
  }
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeDrawer();
  });

  /* ---------- 阅读进度 ---------- */
  var bar = $("#progress");
  var toTop = $("#toTop");
  function onScroll() {
    var h = document.documentElement;
    var max = h.scrollHeight - h.clientHeight;
    var y = h.scrollTop || document.body.scrollTop;
    if (bar && max > 0) bar.style.width = Math.min(100, (y / max) * 100) + "%";
    if (toTop) toTop.classList.toggle("is-on", y > 700);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
  if (toTop) {
    toTop.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  /* ---------- 入场上浮 ---------- */
  var reveals = $$(".reveal");
  if ("IntersectionObserver" in window && reveals.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          en.target.classList.add("is-in");
          io.unobserve(en.target);
        }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.05 });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add("is-in"); });
  }

  /* ---------- 目录滚动高亮 ---------- */
  var railLinks = $$(".rail a, .toc-mobile a");
  if (railLinks.length && "IntersectionObserver" in window) {
    var map = {};
    railLinks.forEach(function (a) {
      var id = (a.getAttribute("href") || "").replace("#", "");
      if (id) map[id] = a;
    });
    var targets = $$(".prose h2[id]");
    var so = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        var a = map[en.target.id];
        if (!a) return;
        railLinks.forEach(function (x) { x.classList.remove("is-active"); });
        a.classList.add("is-active");
      });
    }, { rootMargin: "-15% 0px -70% 0px" });
    targets.forEach(function (t) { so.observe(t); });
  }

  /* ---------- 术语词典筛选 ---------- */
  var dict = $("#dict");
  if (dict) {
    var searchEl = $("#dictSearch");
    var chips = $$(".chip[data-part]");
    var countEl = $("#dictCount");
    var entries = $$(".entry", dict);
    var activePart = "all";

    function norm(s) {
      return (s || "").toLowerCase()
        .replace(/[\s\u3000]/g, "")
        .replace(/[，。、；：！？“”‘’（）《》·—…,.;:!?"'()]/g, "");
    }
    function apply() {
      var q = norm(searchEl ? searchEl.value : "");
      var shown = 0;
      entries.forEach(function (el) {
        var okPart = activePart === "all" || (el.getAttribute("data-part") || "").split(" ").indexOf(activePart) > -1;
        var hay = norm(el.getAttribute("data-key") || el.textContent);
        var okQ = !q || hay.indexOf(q) > -1;
        var show = okPart && okQ;
        el.hidden = !show;
        if (show) shown++;
      });
      if (countEl) countEl.textContent = "收录 " + shown + " 条";
    }
    if (searchEl) searchEl.addEventListener("input", apply);
    chips.forEach(function (c) {
      c.addEventListener("click", function () {
        chips.forEach(function (x) { x.classList.remove("is-on"); });
        c.classList.add("is-on");
        activePart = c.getAttribute("data-part");
        apply();
      });
    });
    apply();
  }

  /* ---------- 概念网络 ---------- */
  var net = $("#net");
  if (net && window.NET_DATA) {
    var data = window.NET_DATA;
    var nodes = $$(".net-node", net);
    var edges = $$(".net-edge", net);
    var panel = $("#netPanel");

    function showNode(id) {
      var n = data.nodes.filter(function (x) { return x.id === id; })[0];
      if (!n) return;
      nodes.forEach(function (g) { g.classList.toggle("is-on", g.getAttribute("data-id") === id); });
      edges.forEach(function (e) {
        var d = e.getAttribute("data-edge") || "";
        e.classList.toggle("is-on", d.split("|").indexOf(id) > -1);
      });
      if (!panel) return;
      var rel = data.edges.filter(function (e) { return e[0] === id || e[1] === id; });
      var links = rel.map(function (e) {
        var other = e[0] === id ? e[1] : e[0];
        var name = (data.nodes.filter(function (x) { return x.id === other; })[0] || {}).cn || other;
        return '<a href="#' + other + '" data-jump="' + other + '">' + name + " · " + e[2] + "</a>";
      }).join("");
      panel.innerHTML =
        '<div class="np-k">概念节点</div>' +
        "<h3>" + n.cn + "</h3>" +
        '<div class="de">' + n.de + "</div>" +
        "<p>" + n.def + "</p>" +
        '<div class="np-k">原著位置</div><p style="font-size:.76rem">' + n.loc + "</p>" +
        '<div class="links">' + links + "</div>" +
        '<p style="margin-top:.7rem"><a href="' + n.url + '">进入概念专题 →</a></p>';
      if (window.innerWidth < 760) {
        panel.scrollIntoView({ behavior: "smooth", block: "center" });
      }
      $$("#netPanel [data-jump]").forEach(function (a) {
        a.addEventListener("click", function (ev) {
          ev.preventDefault();
          showNode(a.getAttribute("data-jump"));
        });
      });
    }
    nodes.forEach(function (g) {
      g.addEventListener("click", function () { showNode(g.getAttribute("data-id")); });
      g.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); showNode(g.getAttribute("data-id")); }
      });
    });
    if (panel && !panel.innerHTML.trim()) {
      panel.innerHTML = '<div class="np-k">概念节点</div><h3>选择左侧或图中的节点</h3>' +
        '<p>每个节点都给出简要定义、原著节号与相关概念。图中共 25 个关键范畴，连线标出它们之间的过渡、映现与包含关系。</p>';
    }
  }

  /* ---------- 推演步骤筛选 ---------- */
  var steps = $$(".step[data-part]");
  if (steps.length) {
    var fchips = $$("[data-filter]");
    fchips.forEach(function (c) {
      c.addEventListener("click", function () {
        fchips.forEach(function (x) { x.classList.remove("is-on"); });
        c.classList.add("is-on");
        var p = c.getAttribute("data-filter");
        steps.forEach(function (s) {
          s.hidden = !(p === "all" || s.getAttribute("data-part") === p);
        });
      });
    });
  }

  /* ---------- 当前页导航 ---------- */
  var here = location.pathname.split("/").pop() || "index.html";
  $$(".nav a, .drawer a").forEach(function (a) {
    var href = (a.getAttribute("href") || "").split("/").pop();
    if (href === here) a.setAttribute("aria-current", "page");
  });
})();
