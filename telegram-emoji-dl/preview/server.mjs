// Anteprima locale: griglia animata di tutte le emoji in public/lottie (lottie-web da node_modules, nessuna CDN).
// Uso: npm run preview [-- <emoji o id>]    es. npm run preview -- 🚀   oppure   npm run preview -- 1f680
import { createServer } from "node:http";
import { existsSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { dirname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const LOTTIE_DIR = join(ROOT, "public", "lottie");
const LOTTIE_WEB = join(ROOT, "node_modules", "lottie-web", "build", "player", "lottie.min.js");
const PORT = Number(process.env.PORT ?? 5173);
const TYPES = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".json": "application/json" };

// Risolve un URL in un file locale consentito (pagina, lottie-web, JSON Lottie)
function resolvePath(url) {
  if (url === "/") return join(ROOT, "preview", "index.html");
  if (url === "/vendor/lottie.js") return LOTTIE_WEB;
  if (!url.startsWith("/lottie/")) return null;
  const path = normalize(join(LOTTIE_DIR, url.slice("/lottie/".length)));
  return path.startsWith(LOTTIE_DIR) ? path : null; // blocca path traversal
}

async function handle(req, res) {
  if (req.url === "/favicon.ico") return void res.writeHead(204).end(); // niente favicon: evita un 404 in console
  try {
    const path = resolvePath(decodeURIComponent(new URL(req.url, "http://x").pathname));
    if (!path || !existsSync(path)) throw new Error("not found");
    const ext = path.slice(path.lastIndexOf("."));
    res.writeHead(200, { "content-type": TYPES[ext] ?? "application/octet-stream" }).end(await readFile(path));
  } catch {
    res.writeHead(404).end("not found");
  }
}

function main() {
  if (!existsSync(join(LOTTIE_DIR, "manifest.json"))) {
    console.error("manifest.json mancante: lancia prima download.py e convert.py");
    process.exit(1);
  }
  const query = process.argv[2] ? `/?q=${encodeURIComponent(process.argv[2])}` : "/";
  createServer(handle).listen(PORT, "127.0.0.1", () => console.log(`Anteprima: http://127.0.0.1:${PORT}${query}`));
}

main();
