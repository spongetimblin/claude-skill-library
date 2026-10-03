// Minimal headless Chrome driver over the DevTools protocol. No dependencies (Node 22+).
// Nothing appears on screen. Each open() starts its own Chrome with a throwaway profile.
//
//   import { open } from "../_tools/cdp.mjs";
//   const page = await open(url, { width: 1280, height: 800, dark: false, mobile: false, preload: "js run before the page" });
//   await page.eval("expr");            // returns the value; awaits promises
//   await page.waitFor("expr", 10000);  // polls until truthy
//   await page.shot("out.png", true);   // true = full page
//   await page.key("z"); await page.click(x, y);
//   page.logs                           // console messages, exceptions, failed loads
//   await page.close();                 // always close, or Chrome keeps running
import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync, readFileSync, existsSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
// The timer is cleared when the call settles, so a finished script exits at once instead of waiting it out.
const withTimeout = (p, ms, what) => {
  let t;
  return Promise.race([p, new Promise((_, rej) => { t = setTimeout(() => rej(new Error(what + " timed out after " + ms + " ms")), ms); })]).finally(() => clearTimeout(t));
};

export async function open(url, opts = {}) {
  const { width = 1280, height = 800, dark = false, mobile = false, preload = null } = opts;
  const profile = mkdtempSync(join(tmpdir(), "cdp-"));
  // Port 0 lets Chrome pick a free port, so parallel runs and leftover Chromes cannot collide.
  const proc = spawn(CHROME, [
    "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
    "--autoplay-policy=no-user-gesture-required", "--mute-audio",
    "--remote-debugging-port=0", `--user-data-dir=${profile}`,
    `--window-size=${width},${height}`, "about:blank",
  ], { stdio: "ignore" });
  const kill = () => { try { proc.kill("SIGKILL"); } catch (e) {} try { rmSync(profile, { recursive: true, force: true }); } catch (e) {} };

  try {
    const portFile = join(profile, "DevToolsActivePort");
    let port = null;
    for (let i = 0; i < 150 && !port; i++) {
      await new Promise(r => setTimeout(r, 100));
      if (existsSync(portFile)) port = readFileSync(portFile, "utf8").split("\n")[0].trim();
    }
    if (!port) throw new Error("Chrome did not start");
    let target = null;
    for (let i = 0; i < 50 && !target; i++) {
      try { target = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find(t => t.type === "page"); } catch (e) {}
      if (!target) await new Promise(r => setTimeout(r, 100));
    }
    if (!target) throw new Error("no page target");

    const ws = new WebSocket(target.webSocketDebuggerUrl);
    await withTimeout(new Promise((res, rej) => { ws.onopen = res; ws.onerror = () => rej(new Error("WebSocket error")); }), 10000, "DevTools connection");
    let id = 0; const pending = new Map(); const logs = [];
    ws.onmessage = ev => {
      const m = JSON.parse(ev.data);
      if (m.id && pending.has(m.id)) { const { res, rej } = pending.get(m.id); pending.delete(m.id); m.error ? rej(new Error(m.error.message)) : res(m.result); }
      else if (m.method === "Runtime.consoleAPICalled") logs.push({ type: m.params.type, text: m.params.args.map(a => a.value ?? a.description ?? "").join(" ") });
      else if (m.method === "Runtime.exceptionThrown") logs.push({ type: "exception", text: m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text });
      else if (m.method === "Log.entryAdded") logs.push({ type: "log:" + m.params.entry.level, text: m.params.entry.text + " " + (m.params.entry.url || "") });
    };
    const send = (method, params = {}) => withTimeout(new Promise((res, rej) => { const i = ++id; pending.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params })); }), 120000, method);

    await send("Page.enable"); await send("Runtime.enable"); await send("Log.enable");
    await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: mobile ? 2 : 1, mobile });
    if (mobile) await send("Emulation.setTouchEmulationEnabled", { enabled: true });
    await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-color-scheme", value: dark ? "dark" : "light" }] });

    const page = {
      logs, send,
      async goto(u) {
        await send("Page.navigate", { url: u });
        await page.waitFor("document.readyState === 'complete'", 20000);
      },
      async eval(expr, awaitPromise = true) {
        const r = await send("Runtime.evaluate", { expression: expr, awaitPromise, returnByValue: true, userGesture: true });
        if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
        return r.result.value;
      },
      async waitFor(expr, ms = 10000) {
        const t0 = Date.now();
        while (Date.now() - t0 < ms) {
          try { if (await page.eval(expr)) return true; } catch (e) {}
          await new Promise(r => setTimeout(r, 100));
        }
        throw new Error("waitFor timed out: " + expr);
      },
      async shot(file, full = false) {
        let clip;
        if (full) {
          const m = await send("Page.getLayoutMetrics");
          clip = { x: 0, y: 0, width: m.cssContentSize.width, height: Math.min(m.cssContentSize.height, 12000), scale: 1 };
        }
        const r = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: !!full, clip });
        writeFileSync(file, Buffer.from(r.data, "base64"));
      },
      async key(key, o = {}) {
        const code = o.code || (key.length === 1 ? "Key" + key.toUpperCase() : key);
        const base = { key, code, windowsVirtualKeyCode: o.vk || 0, text: o.text };
        await send("Input.dispatchKeyEvent", { type: "keyDown", ...base });
        if (o.hold) await new Promise(r => setTimeout(r, o.hold));
        await send("Input.dispatchKeyEvent", { type: "keyUp", ...base });
      },
      async click(x, y) {
        await send("Input.dispatchMouseEvent", { type: "mousePressed", x, y, button: "left", clickCount: 1 });
        await send("Input.dispatchMouseEvent", { type: "mouseReleased", x, y, button: "left", clickCount: 1 });
      },
      async sleep(ms) { await new Promise(r => setTimeout(r, ms)); },
      async close() { try { ws.close(); } catch (e) {} await new Promise(r => setTimeout(r, 200)); kill(); },
    };
    if (preload) await send("Page.addScriptToEvaluateOnNewDocument", { source: preload });
    await page.goto(url);
    return page;
  } catch (e) {
    kill();   // never leave a Chrome behind when startup fails
    throw e;
  }
}
