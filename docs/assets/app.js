/* paknevis playground: runs the real Python package in the browser via Pyodide. */
(() => {
  "use strict";

  const PYODIDE_VERSION = "0.29.5";
  const PYODIDE_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
  const BUNDLE_URL = "assets/py/paknevis.zip";
  const ZWNJ = "\u200c";

  const I18N = {
    fa: {
      skip: "پرش به ویرایشگر",
      tagline: "ویراستار خودکار متن فارسی — مثل Prettier و ESLint، برای نوشتار فارسی",
      docs: "مستندات",
      "status.idle": "در انتظار بارگذاری موتور…",
      "status.runtime": "در حال بارگیری پایتون (Pyodide)…",
      "status.packages": "در حال بارگذاری PyYAML…",
      "status.paknevis": "در حال نصب پاک‌نویس…",
      "status.ready": "آماده · پاک‌نویس {v} روی پایتون {py}",
      "status.error": "بارگذاری موتور ناموفق بود: {e}",
      "opt.syntax": "قالب",
      "syntax.plain": "متن ساده",
      "opt.digits": "رقم‌ها",
      "digits.persian": "فارسی ۱۲۳",
      "digits.latin": "لاتین 123",
      "digits.keep": "دست نزن",
      "opt.ezafe": "کسرهٔ اضافه",
      "opt.invisibles": "نمایش نیم‌فاصله",
      "opt.rules": "قاعده‌ها",
      samples: "نمونه‌ها:",
      "sample.blog": "نوشتهٔ وبلاگ",
      "sample.markdown": "README مارک‌داون",
      "sample.latex": "پایان‌نامهٔ LaTeX",
      "sample.html": "صفحهٔ HTML",
      "sample.clear": "پاک کردن",
      input: "متن ورودی",
      placeholder: "متن فارسی خود را این‌جا بنویسید یا جای‌گذاری کنید…",
      "tab.issues": "مشکلات",
      "tab.fixed": "متن اصلاح‌شده",
      apply: "اعمال اصلاح‌ها",
      copy: "رونوشت",
      copied: "رونوشت شد ✓",
      "list.title": "فهرست مشکلات",
      "list.empty": "هیچ مشکلی پیدا نشد. ✨",
      "install.title": "در پروژهٔ خودتان",
      "install.body": "همین موتور به‌صورت کتابخانهٔ پایتون، خط فرمان، هوک pre-commit و GitHub Action در دسترس است.",
      footer: "همه‌چیز در مرورگر شما اجرا می‌شود (Pyodide)؛ متنی به سروری فرستاده نمی‌شود.",
      made: "ساخته‌شده به دست",
      font: "قلم",
      meta: "{c} نویسه · {l} سطر",
      waiting: "موتور در حال بارگذاری است؛ نتیجه به‌زودی این‌جا نمایش داده می‌شود…",
      emptyInput: "متنی برای بررسی وجود ندارد.",
      fix: "پیشنهاد",
      noFix: "بدون اصلاح خودکار",
      line: "سطر",
      toggleLang: "English",
      categories: { characters: "نویسه‌ها", zwnj: "نیم‌فاصله", punctuation: "نشانه‌گذاری", whitespace: "فاصله‌ها", spelling: "املا" },
    },
    en: {
      skip: "Skip to editor",
      tagline: "Persian text linter & auto-fixer — like Prettier/ESLint, for Persian writing",
      docs: "Docs",
      "status.idle": "Waiting to load the engine…",
      "status.runtime": "Downloading Python (Pyodide)…",
      "status.packages": "Loading PyYAML…",
      "status.paknevis": "Installing paknevis…",
      "status.ready": "Ready · paknevis {v} on Python {py}",
      "status.error": "Failed to load the engine: {e}",
      "opt.syntax": "Syntax",
      "syntax.plain": "Plain text",
      "opt.digits": "Digits",
      "digits.persian": "Persian ۱۲۳",
      "digits.latin": "Latin 123",
      "digits.keep": "Keep",
      "opt.ezafe": "Ezafe",
      "opt.invisibles": "Show ZWNJ",
      "opt.rules": "Rules",
      samples: "Samples:",
      "sample.blog": "Blog post",
      "sample.markdown": "Markdown README",
      "sample.latex": "LaTeX thesis",
      "sample.html": "HTML page",
      "sample.clear": "Clear",
      input: "Input",
      placeholder: "Type or paste Persian text here…",
      "tab.issues": "Issues",
      "tab.fixed": "Fixed text",
      apply: "Apply fixes",
      copy: "Copy",
      copied: "Copied ✓",
      "list.title": "Diagnostics",
      "list.empty": "No issues found. ✨",
      "install.title": "Use it in your project",
      "install.body": "The same engine ships as a Python library, a CLI, a pre-commit hook and a GitHub Action.",
      footer: "Everything runs in your browser (Pyodide); no text is sent to any server.",
      made: "Made by",
      font: "Font",
      meta: "{c} chars · {l} lines",
      waiting: "The engine is loading; results will appear here shortly…",
      emptyInput: "Nothing to check yet.",
      fix: "Fix",
      noFix: "no automatic fix",
      line: "line",
      toggleLang: "فارسی",
      categories: { characters: "Characters", zwnj: "ZWNJ", punctuation: "Punctuation", whitespace: "Whitespace", spelling: "Spelling" },
    },
  };

  const $ = (id) => document.getElementById(id);
  const els = {
    input: $("input"),
    issues: $("view-issues"),
    fixed: $("view-fixed"),
    status: $("status"),
    statusText: $("status-text"),
    list: $("diag-list"),
    empty: $("diag-empty"),
    count: $("issue-count"),
    meta: $("input-meta"),
    syntax: $("opt-syntax"),
    digits: $("opt-digits"),
    ezafe: $("opt-ezafe"),
    invisibles: $("opt-invisibles"),
    rulesToggle: $("rules-toggle"),
    rulesPanel: $("rules-panel"),
    rulesCount: $("rules-count"),
    copy: $("copy"),
    apply: $("apply"),
    tooltip: $("tooltip"),
    lang: $("lang-toggle"),
    version: $("engine-version"),
  };

  const state = {
    // Persian-first: default to Persian unless the user explicitly chose English.
    lang: localStorage.getItem("paknevis.lang") || "fa",
    engine: null,
    rules: [],
    disabled: new Set(),
    result: null,
    statusKey: "status.idle",
    statusArgs: {},
    timer: 0,
  };

  const t = (key, args = {}) => {
    const value = I18N[state.lang][key] ?? I18N.en[key] ?? key;
    return typeof value === "string" ? value.replace(/\{(\w+)\}/g, (_, k) => args[k] ?? "") : value;
  };
  const faDigits = (s) => (state.lang === "fa" ? String(s).replace(/\d/g, (d) => "۰۱۲۳۴۵۶۷۸۹"[d]) : String(s));

  // ------------------------------------------------------------------ i18n
  function applyLanguage() {
    const html = document.documentElement;
    html.lang = state.lang;
    html.dir = state.lang === "fa" ? "rtl" : "ltr";
    document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => { el.placeholder = t(el.dataset.i18nPlaceholder); });
    els.lang.textContent = t("toggleLang");
    setStatus(els.status.dataset.state, state.statusKey, state.statusArgs);
    renderRulesPanel();
    updateMeta(els.input.value);
    render();
  }

  function setStatus(kind, key, args = {}) {
    state.statusKey = key;
    state.statusArgs = args;
    els.status.dataset.state = kind;
    els.statusText.textContent = t(key, args);
  }

  // ------------------------------------------------------------------ engine
  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = src;
      script.onload = resolve;
      script.onerror = () => reject(new Error(`cannot load ${src}`));
      document.head.appendChild(script);
    });
  }

  /* The engine (Pyodide + the real paknevis package) runs in a Web Worker so loading it never blocks the page. */
  function loadEngine() {
    if (!window.Worker) return loadEngineMain();
    let worker;
    try { worker = new Worker(new URL("assets/engine-worker.js", document.baseURI).href); } catch { return loadEngineMain(); }
    setStatus("loading", "status.runtime");
    let nextId = 0;
    const pending = new Map();
    worker.onmessage = (ev) => {
      const m = ev.data;
      if (m.type === "status") { setStatus("loading", m.key); return; }
      if (m.type === "ready") {
        state.engine = {
          run: (text, options) => new Promise((resolve, reject) => {
            const id = ++nextId; pending.set(id, { resolve, reject });
            worker.postMessage({ type: "run", id, text, options });
          }),
        };
        state.rules = m.rules;
        els.version.textContent = `paknevis ${m.version} · Pyodide ${PYODIDE_VERSION}`;
        setStatus("ready", "status.ready", { v: m.version, py: m.py });
        document.body.dataset.engine = "ready";
        renderRulesPanel();
        analyse();
        return;
      }
      if (m.type === "result") {
        const p = pending.get(m.id); pending.delete(m.id);
        if (p) { if (m.error) p.reject(new Error(m.error)); else p.resolve(m.result); }
        return;
      }
      if (m.type === "error") {
        console.error(m.message);
        setStatus("error", "status.error", { e: m.message });
        document.body.dataset.engine = "error";
      }
    };
    worker.onerror = (e) => {
      setStatus("error", "status.error", { e: e.message || "worker" });
      document.body.dataset.engine = "error";
    };
    worker.postMessage({ type: "init", pyodideUrl: PYODIDE_URL, bundleUrl: new URL(BUNDLE_URL, document.baseURI).href });
  }

  async function loadEngineMain() {
    try {
      setStatus("loading", "status.runtime");
      await loadScript(`${PYODIDE_URL}pyodide.js`);
      const pyodide = await window.loadPyodide({ indexURL: PYODIDE_URL });
      setStatus("loading", "status.packages");
      await pyodide.loadPackage("pyyaml");
      setStatus("loading", "status.paknevis");
      const response = await fetch(BUNDLE_URL, { cache: "no-cache" });
      if (!response.ok) throw new Error(`HTTP ${response.status} for ${BUNDLE_URL}`);
      pyodide.unpackArchive(await response.arrayBuffer(), "zip", { extractDir: "/home/pyodide/paknevis-src" });
      pyodide.runPython("import sys; sys.path.insert(0, '/home/pyodide/paknevis-src')");
      const web = pyodide.pyimport("paknevis.web");
      const version = pyodide.runPython("import paknevis; paknevis.__version__");
      const py = pyodide.runPython("import platform; platform.python_version()");
      state.engine = { run: (text, options) => JSON.parse(web.run(text, JSON.stringify(options))) };
      state.rules = JSON.parse(web.rules_json());
      els.version.textContent = `paknevis ${version} · Pyodide ${PYODIDE_VERSION}`;
      setStatus("ready", "status.ready", { v: version, py });
      document.body.dataset.engine = "ready";
      renderRulesPanel();
      analyse();
    } catch (error) {
      console.error(error);
      setStatus("error", "status.error", { e: error.message || String(error) });
      document.body.dataset.engine = "error";
    }
  }

  // ------------------------------------------------------------------ analysis
  function options() {
    return {
      syntax: els.syntax.value,
      digits: els.digits.value,
      ezafe: els.ezafe.value,
      disable: [...state.disabled],
    };
  }

  async function analyse() {
    const text = els.input.value;
    const seq = state.seq = (state.seq || 0) + 1;
    updateMeta(text);
    saveHash();
    if (!state.engine) { render(); return; }
    try {
      const result = await state.engine.run(text, options());
      if (seq !== state.seq) return; // a newer analysis superseded this one
      state.result = result;
      state.result.input = text;
    } catch (error) {
      console.error(error);
      state.result = null;
    }
    render();
  }

  const schedule = () => { clearTimeout(state.timer); state.timer = setTimeout(analyse, 180); };

  function updateMeta(text) {
    const chars = [...text].length;
    const lines = text ? text.split("\n").length : 0;
    els.meta.textContent = t("meta", { c: faDigits(chars), l: faDigits(lines) });
  }

  // Map code-point offsets (Python) to UTF-16 indices (JavaScript).
  function codePointIndex(text) {
    const map = [0];
    let index = 0;
    for (const ch of text) { index += ch.length; map.push(index); }
    return (cp) => map[Math.min(cp, map.length - 1)];
  }

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  }

  function visible(s, marked) {
    let html = escapeHtml(s);
    if (els.invisibles.checked) html = html.split(ZWNJ).join(`<span class="zw" title="ZWNJ">${ZWNJ}</span>`);
    if (marked) html = html.replace(/ /g, '<span class="ws">·</span>').replace(/\t/g, '<span class="ws">⇥</span>');
    return html;
  }

  function renderIssues(result) {
    const text = result.input;
    const idx = codePointIndex(text);
    const diags = result.diagnostics;
    const points = new Set([0, text.length]);
    diags.forEach((d) => { points.add(idx(d.offset)); points.add(idx(d.end_offset)); });
    const sorted = [...points].sort((a, b) => a - b);
    let html = "";
    // zero-width diagnostics → caret markers
    const carets = new Map();
    diags.forEach((d, i) => { if (d.offset === d.end_offset) carets.set(idx(d.offset), i); });
    for (let k = 0; k < sorted.length - 1; k++) {
      const start = sorted[k];
      const end = sorted[k + 1];
      if (carets.has(start)) html += `<mark class="issue caret ${diags[carets.get(start)].severity}" data-i="${carets.get(start)}"></mark>`;
      const covering = [];
      diags.forEach((d, i) => { if (idx(d.offset) <= start && idx(d.end_offset) >= end && d.offset !== d.end_offset) covering.push(i); });
      const piece = text.slice(start, end);
      if (!covering.length) { html += visible(piece, false); continue; }
      const worst = covering.map((i) => diags[i].severity).sort((a, b) => rank(b) - rank(a))[0];
      html += `<mark class="issue ${worst}" data-i="${covering.join(",")}">${visible(piece, true)}</mark>`;
    }
    return html || `<span class="placeholder">${escapeHtml(t("emptyInput"))}</span>`;
  }

  const rank = (s) => ({ info: 0, warning: 1, error: 2 })[s] ?? 0;

  function renderFixed(result) {
    const fixed = result.fixed;
    const idx = codePointIndex(fixed);
    let html = "";
    let cursor = 0;
    for (const [fs, fe] of result.changes) {
      const a = idx(fs);
      const b = idx(fe);
      html += visible(fixed.slice(cursor, a), false);
      if (b > a) html += `<mark class="added">${visible(fixed.slice(a, b), false)}</mark>`;
      cursor = b;
    }
    html += visible(fixed.slice(cursor), false);
    return html || `<span class="placeholder">${escapeHtml(t("emptyInput"))}</span>`;
  }

  function message(d) { return state.lang === "fa" ? d.message_fa : d.message; }
  function show(s) { return s.split(ZWNJ).join("⟨ZWNJ⟩").replace(/ /g, "·").replace(/\n/g, "⏎") || "∅"; }

  function render() {
    const result = state.result;
    if (!state.engine || !result) {
      const waiting = `<span class="placeholder">${escapeHtml(state.engine ? t("emptyInput") : t("waiting"))}</span>`;
      els.issues.innerHTML = waiting;
      els.fixed.innerHTML = waiting;
      els.list.innerHTML = "";
      els.empty.hidden = !state.engine;
      els.count.textContent = "…";
      els.copy.disabled = els.apply.disabled = true;
      return;
    }
    els.issues.innerHTML = renderIssues(result);
    els.fixed.innerHTML = renderFixed(result);
    const n = result.diagnostics.length;
    els.count.textContent = faDigits(n);
    els.count.classList.toggle("zero", n === 0);
    els.copy.disabled = !result.fixed;
    els.apply.disabled = result.fixed === result.input;
    els.empty.hidden = n > 0 || !result.input;
    els.list.innerHTML = result.diagnostics.map((d, i) => `
      <li data-i="${i}" tabindex="0">
        <span class="sev ${d.severity}">${d.severity}</span>
        <span class="rule-id">${d.code} ${d.rule}</span>
        <span>${escapeHtml(message(d))}</span>
        <span class="diag-fix">${d.fixable ? `<bdi dir="rtl">«${escapeHtml(show(d.original))}» ← «<b>${escapeHtml(show(d.replacement))}</b>»</bdi>` : escapeHtml(t("noFix"))}
          <span class="loc">${d.line}:${d.column}</span></span>
      </li>`).join("");
  }

  // ------------------------------------------------------------------ rules panel
  function renderRulesPanel() {
    if (!state.rules.length) { els.rulesCount.textContent = ""; return; }
    const groups = {};
    state.rules.forEach((r) => { (groups[r.category] ||= []).push(r); });
    const cats = t("categories");
    els.rulesPanel.innerHTML = Object.entries(groups).map(([cat, rules]) => `
      <h3>${escapeHtml(cats[cat] || cat)}</h3>
      ${rules.map((r) => `<label title="${escapeHtml(state.lang === "fa" ? r.description_fa : r.description_en)}">
        <input type="checkbox" data-rule="${r.name}" ${state.disabled.has(r.name) ? "" : "checked"}>
        <span>${escapeHtml(state.lang === "fa" ? r.title_fa : r.title_en)} <code>${r.code}</code></span></label>`).join("")}
    `).join("");
    els.rulesCount.textContent = faDigits(`${state.rules.length - state.disabled.size}/${state.rules.length}`);
  }

  // ------------------------------------------------------------------ interactions
  function highlight(indices, on) {
    document.querySelectorAll("mark.issue.active, .diag-list li.active").forEach((el) => el.classList.remove("active"));
    if (!on) return;
    indices.forEach((i) => {
      document.querySelectorAll("mark.issue").forEach((m) => { if (m.dataset.i.split(",").includes(String(i))) m.classList.add("active"); });
      const li = els.list.querySelector(`li[data-i="${i}"]`);
      if (li) li.classList.add("active");
    });
  }

  function showTooltip(mark, x, y) {
    const result = state.result;
    if (!result) return;
    const items = mark.dataset.i.split(",").map((i) => result.diagnostics[Number(i)]);
    els.tooltip.innerHTML = items.map((d) => `<div>${escapeHtml(message(d))} <code>${d.code}</code></div>`).join("");
    els.tooltip.hidden = false;
    const rect = els.tooltip.getBoundingClientRect();
    els.tooltip.style.left = `${Math.max(8, Math.min(x - rect.width / 2, innerWidth - rect.width - 8))}px`;
    els.tooltip.style.top = `${y + 18 + rect.height > innerHeight ? y - rect.height - 12 : y + 18}px`;
  }

  function selectTab(name) {
    const issues = name === "issues";
    $("tab-issues").setAttribute("aria-selected", String(issues));
    $("tab-fixed").setAttribute("aria-selected", String(!issues));
    els.issues.hidden = !issues;
    els.fixed.hidden = issues;
  }

  // URL hash: #s=<syntax>&t=<base64url text>
  function saveHash() {
    const text = els.input.value;
    if (!text || text.length > 4000) { history.replaceState(null, "", location.pathname); return; }
    const bytes = new TextEncoder().encode(text);
    let bin = "";
    bytes.forEach((b) => { bin += String.fromCharCode(b); });
    const encoded = btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
    history.replaceState(null, "", `#s=${els.syntax.value}&t=${encoded}`);
  }

  function loadHash() {
    const params = new URLSearchParams(location.hash.slice(1));
    const encoded = params.get("t");
    if (params.get("s")) els.syntax.value = params.get("s");
    if (!encoded) return false;
    try {
      const bin = atob(encoded.replace(/-/g, "+").replace(/_/g, "/"));
      els.input.value = new TextDecoder().decode(Uint8Array.from(bin, (c) => c.charCodeAt(0)));
      return true;
    } catch { return false; }
  }

  function loadSample(name) {
    const sample = window.PAKNEVIS_SAMPLES[name];
    if (!sample) return;
    if (sample.syntax) els.syntax.value = sample.syntax;
    els.input.value = sample.text;
    analyse();
    els.input.focus();
  }

  els.input.addEventListener("input", schedule);
  [els.syntax, els.digits, els.ezafe].forEach((el) => el.addEventListener("change", analyse));
  els.invisibles.addEventListener("change", render);
  els.lang.addEventListener("click", () => {
    state.lang = state.lang === "fa" ? "en" : "fa";
    localStorage.setItem("paknevis.lang", state.lang);
    applyLanguage();
  });
  document.querySelectorAll("[data-sample]").forEach((btn) => btn.addEventListener("click", () => loadSample(btn.dataset.sample)));
  $("tab-issues").addEventListener("click", () => selectTab("issues"));
  $("tab-fixed").addEventListener("click", () => selectTab("fixed"));
  els.rulesToggle.addEventListener("click", () => {
    const open = els.rulesPanel.hidden;
    els.rulesPanel.hidden = !open;
    els.rulesToggle.setAttribute("aria-expanded", String(open));
  });
  els.rulesPanel.addEventListener("change", (event) => {
    const box = event.target.closest("input[data-rule]");
    if (!box) return;
    if (box.checked) state.disabled.delete(box.dataset.rule); else state.disabled.add(box.dataset.rule);
    els.rulesCount.textContent = faDigits(`${state.rules.length - state.disabled.size}/${state.rules.length}`);
    analyse();
  });
  els.copy.addEventListener("click", async () => {
    if (!state.result) return;
    try { await navigator.clipboard.writeText(state.result.fixed); } catch { /* clipboard unavailable */ }
    els.copy.textContent = t("copied");
    setTimeout(() => { els.copy.textContent = t("copy"); }, 1500);
  });
  els.apply.addEventListener("click", () => {
    if (!state.result) return;
    els.input.value = state.result.fixed;
    analyse();
  });
  els.issues.addEventListener("mousemove", (event) => {
    const mark = event.target.closest("mark.issue");
    if (mark) showTooltip(mark, event.clientX, event.clientY); else els.tooltip.hidden = true;
  });
  els.issues.addEventListener("mouseleave", () => { els.tooltip.hidden = true; });
  els.list.addEventListener("click", (event) => {
    const li = event.target.closest("li[data-i]");
    if (!li) return;
    selectTab("issues");
    highlight([Number(li.dataset.i)], true);
    const mark = [...document.querySelectorAll("mark.issue")].find((m) => m.dataset.i.split(",").includes(li.dataset.i));
    if (mark) mark.scrollIntoView({ block: "center", behavior: "smooth" });
  });
  els.list.addEventListener("keydown", (event) => { if (event.key === "Enter") event.target.click(); });

  // ------------------------------------------------------------------ boot
  if (!loadHash()) loadSample("blog");
  applyLanguage();
  const start = () => loadEngine();
  if ("requestIdleCallback" in window) requestIdleCallback(start, { timeout: 1200 }); else setTimeout(start, 300);
})();
