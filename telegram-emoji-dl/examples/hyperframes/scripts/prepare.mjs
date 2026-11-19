// Prepara la composizione per UN'emoji: copia il JSON, compila src/emoji.ts e genera index.html.
// Uso: npm run prepare:emoji -- <set> <id>     (es. animated_emoji 1f600)
import { build } from "esbuild";
import { copyFile, mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = join(dirname(fileURLToPath(import.meta.url)), "..");
const LOTTIE_DIR = join(HERE, "..", "..", "public", "lottie");

// Trova l'emoji nel manifest generato da convert.py
async function findEntry(set, id) {
  const manifest = JSON.parse(await readFile(join(LOTTIE_DIR, "manifest.json"), "utf8"));
  const entry = manifest.find((e) => e.set === set && e.id === id);
  if (!entry) throw new Error(`Emoji "${id}" non trovata nel set "${set}" (vedi public/lottie/manifest.json)`);
  return entry;
}

// Compila due file locali per il browser (nessuna CDN):
// - vendor/libs.min.js: lottie-web + gsap (il lint di HyperFrames salta vendor/ e *.min.js: sono librerie di terze parti)
// - dist/emoji.js: il codice della composizione (src/emoji.ts), leggibile e controllato dal lint
async function bundle() {
  const common = { bundle: true, format: "iife", target: "chrome120", logLevel: "warning" };
  await build({ ...common, entryPoints: [join(HERE, "src", "libs.ts")], outfile: join(HERE, "vendor", "libs.min.js"), minify: true });
  await build({ ...common, entryPoints: [join(HERE, "src", "emoji.ts")], outfile: join(HERE, "dist", "emoji.js") });
}

// Genera index.html dal template con durata (secondi) e fps del Lottie
async function writeIndex(entry) {
  const template = await readFile(join(HERE, "scripts", "index.template.html"), "utf8");
  const html = template.replace("{{DURATION}}", String(entry.durationInSeconds)).replace("{{FPS}}", String(entry.fps));
  await writeFile(join(HERE, "index.html"), html);
}

async function main() {
  const [set = "animated_emoji", id = "1f600"] = process.argv.slice(2);
  const entry = await findEntry(set, id);
  await mkdir(join(HERE, "assets"), { recursive: true });
  await copyFile(join(LOTTIE_DIR, entry.file), join(HERE, "assets", "emoji.json"));
  await bundle();
  await writeIndex(entry);
  console.log(`Pronto: ${entry.emoji || entry.id} (${set}/${id}) - ${entry.durationInSeconds}s a ${entry.fps} fps`);
}

main().catch((err) => { console.error(err.message); process.exit(1); });
