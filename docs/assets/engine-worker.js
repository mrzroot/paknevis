/* paknevis engine worker: runs Pyodide + the real paknevis package off the main thread so the page stays responsive while it loads. */
"use strict";
let web = null;
function status(key) { postMessage({ type: "status", key }); }
async function init(msg) {
  try {
    status("status.runtime");
    importScripts(msg.pyodideUrl + "pyodide.js");
    const pyodide = await loadPyodide({ indexURL: msg.pyodideUrl });
    status("status.packages");
    await pyodide.loadPackage("pyyaml");
    status("status.paknevis");
    const response = await fetch(msg.bundleUrl, { cache: "no-cache" });
    if (!response.ok) throw new Error("HTTP " + response.status + " for " + msg.bundleUrl);
    pyodide.unpackArchive(await response.arrayBuffer(), "zip", { extractDir: "/home/pyodide/paknevis-src" });
    pyodide.runPython("import sys; sys.path.insert(0, '/home/pyodide/paknevis-src')");
    web = pyodide.pyimport("paknevis.web");
    const version = pyodide.runPython("import paknevis; paknevis.__version__");
    const py = pyodide.runPython("import platform; platform.python_version()");
    postMessage({ type: "ready", version: String(version), py: String(py), rules: JSON.parse(web.rules_json()) });
  } catch (e) {
    postMessage({ type: "error", message: (e && e.message) || String(e) });
  }
}
onmessage = (ev) => {
  const m = ev.data;
  if (m.type === "init") { init(m); return; }
  if (m.type === "run") {
    try { postMessage({ type: "result", id: m.id, result: JSON.parse(web.run(m.text, JSON.stringify(m.options))) }); }
    catch (e) { postMessage({ type: "result", id: m.id, error: (e && e.message) || String(e) }); }
  }
};
