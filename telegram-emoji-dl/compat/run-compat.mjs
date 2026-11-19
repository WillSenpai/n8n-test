// Test di compatibilità: carica ogni JSON in lottie-web (headless Chrome) e scrive compat-report.json.
import { createServer } from "node:http";
import { readFile, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { dirname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const LOTTIE_DIR = join(ROOT, "public", "lottie");
const LOTTIE_WEB = join(ROOT, "node_modules", "lottie-web", "build", "player", "lottie.min.js");
const TIMEOUT_MS = 20000;

// Server statico locale: pagina di test, lottie-web da node_modules e JSON da public/lottie (nessun URL remoto)
function startServer() {
  const server = createServer(async (req, res) => {
    try {
      const url = decodeURIComponent(new URL(req.url, "http://x").pathname);
      let path;
      if (url === "/") path = join(ROOT, "compat", "compat.html");
      else if (url === "/vendor/lottie.js") path = LOTTIE_WEB;
      else if (url.startsWith("/lottie/")) path = normalize(join(LOTTIE_DIR, url.slice("/lottie/".length)));
      if (!path || (url.startsWith("/lottie/") && !path.startsWith(LOTTIE_DIR))) throw new Error("not found");
      const type = path.endsWith(".json") ? "application/json" : path.endsWith(".js") ? "text/javascript" : "text/html";
      res.writeHead(200, { "content-type": type }).end(await readFile(path));
    } catch {
      res.writeHead(404).end("not found");
    }
  });
  return new Promise((resolve) => server.listen(0, "127.0.0.1", () => resolve(server)));
}

// Esegue il test con timeout, raccogliendo gli errori di console della pagina
async function testOne(page, item, consoleErrors) {
  consoleErrors.length = 0;
  const timeout = new Promise((r) => setTimeout(() => r({ ok: false, cause: `timeout dopo ${TIMEOUT_MS / 1000}s` }), TIMEOUT_MS));
  const result = await Promise.race([page.evaluate((f) => window.testFile(f), item.file), timeout]);
  if (!result.ok && consoleErrors.length) result.cause += ` | console: ${consoleErrors.join(" ; ")}`;
  return result;
}

function launchOptions() {
  const opts = { args: [] };
  if (process.env.CHROME_PATH) opts.executablePath = process.env.CHROME_PATH;
  if (process.getuid?.() === 0) opts.args.push("--no-sandbox"); // necessario nei container eseguiti come root
  return opts;
}

async function main() {
  const manifestPath = join(LOTTIE_DIR, "manifest.json");
  if (!existsSync(manifestPath)) throw new Error("manifest.json mancante: lancia prima convert.py");
  if (!existsSync(LOTTIE_WEB)) throw new Error("lottie-web mancante: lancia npm install");
  const manifest = JSON.parse(await readFile(manifestPath, "utf8"));

  const server = await startServer();
  const browser = await chromium.launch(launchOptions());
  const page = await browser.newPage();
  const consoleErrors = [];
  page.on("console", (m) => m.type() === "error" && consoleErrors.push(m.text()));
  page.on("pageerror", (e) => consoleErrors.push(e.message));
  await page.goto(`http://127.0.0.1:${server.address().port}/`);

  const ok = [], failed = [];
  for (const item of manifest) {
    const r = await testOne(page, item, consoleErrors);
    const base = { file: item.file, emoji: item.emoji };
    if (r.ok) ok.push({ ...base, warnings: r.warnings, frames: r.frames });
    else failed.push({ ...base, cause: r.cause });
  }
  await browser.close();
  server.close();

  const report = { generatedAt: new Date().toISOString(), lottieWeb: "lottie-web (renderer svg)", total: manifest.length, okCount: ok.length, failedCount: failed.length, ok, failed };
  await writeFile(join(ROOT, "compat-report.json"), JSON.stringify(report, null, 2));
  console.log(`Compat lottie-web: ${ok.length} OK, ${failed.length} problematici su ${manifest.length}`);
  for (const f of failed) console.log(`  ✗ ${f.file}: ${f.cause}`);
  if (failed.length) console.log("Nota: i .tgs sono pensati per rlottie; i file problematici potrebbero renderizzare diversamente su lottie-web (usali con cautela).");
}

main().catch((err) => { console.error(err.message); process.exit(1); });
