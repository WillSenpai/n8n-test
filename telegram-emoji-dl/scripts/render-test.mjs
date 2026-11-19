// Render di prova degli esempi + controllo che l'emoji compaia davvero.
// Uso: node scripts/render-test.mjs <remotion|hyperframes> [set] [id]
// Scrive reports/render-<nome>.json con l'esito (letto da verify.py).
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync, statSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { PNG } from "pngjs";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const BACKGROUND = [0x1b, 0x1f, 0x3a]; // sfondo usato da entrambi gli esempi
const MIN_EMOJI_RATIO = 0.002; // almeno lo 0,2% dei pixel deve differire dallo sfondo
const [target, argSet, argId] = process.argv.slice(2);

const readJson = (path) => JSON.parse(readFileSync(path, "utf8"));

// Sceglie l'emoji da provare: argomenti > prima voce OK del compat-report > prima del manifest
function pickEmoji() {
  const manifest = readJson(join(ROOT, "public", "lottie", "manifest.json"));
  if (argSet && argId) return manifest.find((e) => e.set === argSet && e.id === argId);
  const reportPath = join(ROOT, "compat-report.json");
  if (existsSync(reportPath)) {
    const okFiles = new Set(readJson(reportPath).ok.map((o) => o.file));
    const good = manifest.find((e) => okFiles.has(e.file));
    if (good) return good;
  }
  return manifest[0];
}

// Esegue un comando e fallisce con un messaggio chiaro
function run(cmd, args, cwd) {
  const res = spawnSync(cmd, args, { cwd, encoding: "utf8", env: process.env });
  if (res.status !== 0) throw new Error(`${cmd} ${args.join(" ")} -> codice ${res.status}\n${(res.stderr || res.stdout).slice(-1500)}`);
  return res.stdout;
}

// Percentuale di pixel diversi dallo sfondo: se è > soglia, l'emoji è visibile
function emojiRatio(pngPath) {
  const png = PNG.sync.read(readFileSync(pngPath));
  let diff = 0;
  for (let i = 0; i < png.data.length; i += 4) {
    const d = Math.abs(png.data[i] - BACKGROUND[0]) + Math.abs(png.data[i + 1] - BACKGROUND[1]) + Math.abs(png.data[i + 2] - BACKGROUND[2]);
    if (d > 30) diff++;
  }
  return { ratio: diff / (png.width * png.height), width: png.width, height: png.height };
}

function renderRemotion(entry) {
  const dir = join(ROOT, "examples", "remotion");
  const out = join(dir, "out", "still.png");
  const frame = Math.floor(entry.durationInFrames / 2);
  const props = JSON.stringify({ set: entry.set, emojiId: entry.id, animationData: null });
  const args = ["remotion", "still", "src/index.ts", "Emoji", "out/still.png", `--frame=${frame}`, `--props=${props}`];
  if (process.env.CHROME_PATH) args.push(`--browser-executable=${process.env.CHROME_PATH}`);
  run("npx", args, dir);
  return out;
}

function renderHyperframes(entry) {
  const dir = join(ROOT, "examples", "hyperframes");
  mkdirSync(join(dir, "renders"), { recursive: true });
  run("node", ["scripts/prepare.mjs", entry.set, entry.id], dir);
  const video = join(dir, "renders", "test.mp4");
  run("npx", ["hyperframes", "render", "-o", "renders/test.mp4", "--quiet"], dir);
  // Controllo durata/fps del video rispetto al Lottie
  const probe = run("ffprobe", ["-v", "error", "-show_entries", "stream=r_frame_rate,nb_frames", "-of", "csv=p=0", video]).trim();
  const frame = join(dir, "renders", "test-frame.png");
  run("ffmpeg", ["-y", "-v", "error", "-ss", String(entry.durationInSeconds / 2), "-i", video, "-frames:v", "1", frame]);
  return { image: frame, extra: { probe, expectedFps: entry.fps, expectedFrames: entry.durationInFrames } };
}

function main() {
  if (!["remotion", "hyperframes"].includes(target)) throw new Error("Uso: render-test.mjs <remotion|hyperframes> [set] [id]");
  const entry = pickEmoji();
  if (!entry) throw new Error("Nessuna emoji nel manifest: lancia prima convert.py");
  let image, extra = {};
  if (target === "remotion") image = renderRemotion(entry);
  else ({ image, extra } = renderHyperframes(entry));
  const { ratio, width, height } = emojiRatio(image);
  const ok = statSync(image).size > 0 && ratio >= MIN_EMOJI_RATIO && width === 1920 && height === 1080;
  return { ok, target, emoji: `${entry.set}/${entry.id}`, image: relative(ROOT, image), width, height, emojiPixelRatio: Number(ratio.toFixed(4)), ...extra };
}

mkdirSync(join(ROOT, "reports"), { recursive: true });
let result;
try { result = main(); } catch (err) { result = { ok: false, target, error: err.message }; }
writeFileSync(join(ROOT, "reports", `render-${target}.json`), JSON.stringify(result, null, 2));
console.log(result.ok ? `✓ ${target}: emoji visibile (${(result.emojiPixelRatio * 100).toFixed(2)}% dei pixel)` : `✗ ${target}: ${result.error ?? "emoji non visibile"}`);
process.exit(result.ok ? 0 : 1);
