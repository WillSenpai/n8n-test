"""Converte i .tgs in .json (Lottie), .gif trasparente 512x512 e .png del primo frame."""
import argparse
import gzip
import io
import os
import shutil
import subprocess
import tempfile
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from PIL import Image
from tqdm import tqdm

import config


# ---------- Utilità ----------

def non_empty(path: Path) -> bool:
    """True se il file esiste e non è vuoto (usato per saltare il lavoro già fatto)."""
    return path.exists() and path.stat().st_size > 0


def to_square(image: Image.Image) -> Image.Image:
    """Porta l'immagine RGBA a SIZE x SIZE se serve."""
    image = image.convert("RGBA")
    if image.size != (config.SIZE, config.SIZE):
        image = image.resize((config.SIZE, config.SIZE), Image.LANCZOS)
    return image


def frame_to_gif_mode(image: Image.Image) -> Image.Image:
    """RGBA -> immagine a palette con l'indice 255 riservato alla trasparenza."""
    alpha = image.getchannel("A")
    pal = image.convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=255)
    pal.paste(255, mask=alpha.point(lambda a: 255 if a <= 128 else 0))
    return pal


def save_gif(frames: list[Image.Image], fps: float, dest: Path) -> None:
    """Salva i frame RGBA come GIF animata in loop con sfondo trasparente."""
    pal = [frame_to_gif_mode(f) for f in frames]
    duration = max(20, int(round(1000 / fps / 10)) * 10)
    pal[0].save(dest, format="GIF", append_images=pal[1:], save_all=True,
                duration=duration, loop=0, transparency=255, disposal=2)


# ---------- Passi di conversione ----------

def tgs_to_json(src: Path, dest: Path) -> None:
    """Decomprime il .tgs (gzip) nel .json Lottie."""
    with gzip.open(src, "rb") as fin, open(dest, "wb") as fout:
        shutil.copyfileobj(fin, fout)


def load_animation(src: Path):
    """Carica il .tgs con la libreria lottie."""
    from lottie.parsers.tgs import parse_tgs
    return parse_tgs(str(src))


def first_frame_png(src: Path, dest: Path) -> None:
    """Esporta il primo frame come PNG trasparente SIZE x SIZE."""
    from lottie.exporters.cairo import export_png
    anim = load_animation(src)
    buffer = io.BytesIO()
    export_png(anim, buffer, frame=int(anim.in_point))
    buffer.seek(0)
    to_square(Image.open(buffer)).save(dest, format="PNG")


def lottie_frames(src: Path) -> tuple[list[Image.Image], float]:
    """Renderizza tutti i frame con lottie (cairosvg). Restituisce (frame RGBA, fps)."""
    from lottie.exporters.cairo import PngRenderer
    anim = load_animation(src)
    frames = []
    with PngRenderer(anim, 96) as renderer:
        for i in range(int(anim.in_point), int(anim.out_point) + 1):
            buffer = io.BytesIO()
            renderer.serialize(i, buffer)
            buffer.seek(0)
            frames.append(to_square(Image.open(buffer)))
    return frames, anim.frame_rate


# Metodo 1: libreria lottie
def gif_lottie(src: Path, dest: Path) -> None:
    frames, fps = lottie_frames(src)
    save_gif(frames, fps, dest)


# Metodo 2: rlottie-python (opzionale: pip install rlottie-python)
def gif_rlottie(src: Path, dest: Path) -> None:
    from rlottie_python import LottieAnimation
    anim = LottieAnimation.from_tgs(str(src))
    frames = [to_square(anim.render_pillow_frame(i, config.SIZE, config.SIZE))
              for i in range(anim.lottie_animation_get_totalframe())]
    save_gif(frames, anim.lottie_animation_get_framerate(), dest)


# Metodo 3: ffmpeg per la codifica (palette con trasparenza) partendo dai frame lottie
def gif_ffmpeg(src: Path, dest: Path) -> None:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg non trovato nel PATH")
    frames, fps = lottie_frames(src)
    with tempfile.TemporaryDirectory() as tmp:
        for i, frame in enumerate(frames):
            frame.save(Path(tmp) / f"f{i:04d}.png")
        cmd = ["ffmpeg", "-y", "-v", "error", "-framerate", str(fps), "-i", f"{tmp}/f%04d.png",
               "-filter_complex", "split[a][b];[a]palettegen=reserve_transparent=1[p];[b][p]paletteuse",
               "-loop", "0", str(dest)]
        subprocess.run(cmd, check=True, capture_output=True)


GIF_METHODS = (("lottie", gif_lottie), ("rlottie-python", gif_rlottie), ("ffmpeg", gif_ffmpeg))


def make_gif(src: Path, dest: Path) -> tuple[str, list[str]]:
    """Prova i metodi in ordine. Restituisce (metodo riuscito, errori dei metodi falliti)."""
    failures = []
    for name, func in GIF_METHODS:
        try:
            func(src, dest)
            if non_empty(dest):
                return name, failures
            raise RuntimeError("file GIF vuoto")
        except Exception as err:  # noqa: BLE001 - registriamo qualsiasi errore e passiamo al metodo successivo
            failures.append(f"{name}: {type(err).__name__}: {err}")
            dest.unlink(missing_ok=True)
    return "", failures


# ---------- Orchestrazione ----------

def convert_one(src_str: str, force: bool) -> dict:
    """Converte un singolo .tgs. Eseguita in un processo separato."""
    src = Path(src_str)
    set_name, stem = src.parent.name, src.stem
    outputs = {
        "json": config.JSON_DIR / set_name / f"{stem}.json",
        "gif": config.GIF_DIR / set_name / f"{stem}.gif",
        "png": config.PNG_DIR / set_name / f"{stem}.png",
    }
    result = {"file": f"{set_name}/{src.name}", "set": set_name, "ok": {}, "gif_method": "", "errors": []}
    for path in outputs.values():
        path.parent.mkdir(parents=True, exist_ok=True)

    steps = {"json": lambda: tgs_to_json(src, outputs["json"]),
             "png": lambda: first_frame_png(src, outputs["png"])}
    for kind, step in steps.items():
        result["ok"][kind] = _run_step(kind, outputs[kind], step, force, result)

    if non_empty(outputs["gif"]) and not force:
        result["ok"]["gif"], result["gif_method"] = True, "esistente"
    else:
        method, failures = make_gif(src, outputs["gif"])
        result["ok"]["gif"], result["gif_method"] = bool(method), method
        if not method:
            result["errors"].append(f"gif: tutti i metodi falliti -> " + " | ".join(failures))
        elif failures:  # un metodo ha funzionato ma i precedenti no: lo segnaliamo
            result["errors"].append(f"gif: ripiego su '{method}' dopo -> " + " | ".join(failures))
    return result


def _run_step(kind: str, dest: Path, step, force: bool, result: dict) -> bool:
    """Esegue un passo (json/png) saltandolo se già fatto; registra eventuali errori."""
    if non_empty(dest) and not force:
        return True
    try:
        step()
        return non_empty(dest)
    except Exception as err:  # noqa: BLE001
        dest.unlink(missing_ok=True)
        result["errors"].append(f"{kind}: {type(err).__name__}: {err}")
        return False


def list_tgs() -> list[Path]:
    """Elenca tutti i .tgs scaricati (sottocartelle per set)."""
    return sorted(config.TGS_DIR.glob("*/*.tgs"))


def write_errors(results: list[dict]) -> int:
    """Scrive errors.log (una riga per errore). Restituisce il numero di file con almeno un errore."""
    lines = [f"{datetime.now():%Y-%m-%d %H:%M:%S}\t{r['file']}\t{e}" for r in results for e in r["errors"]]
    config.ERRORS_LOG.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return sum(1 for r in results if not all(r["ok"].values()))


def run(force: bool, workers: int) -> list[dict]:
    """Converte tutti i .tgs in parallelo mostrando una barra di avanzamento."""
    files = list_tgs()
    if not files:
        raise SystemExit(f"Nessun .tgs in {config.TGS_DIR}: lancia prima download.py")
    results = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(convert_one, str(f), force) for f in files]
        for future in tqdm(as_completed(futures), total=len(futures), desc="Conversione", unit="file"):
            results.append(future.result())
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Converte i .tgs in json, gif e png.")
    parser.add_argument("--force", action="store_true", help="rigenera anche i file già convertiti")
    parser.add_argument("--workers", type=int, default=os.cpu_count() or 1, help="processi paralleli")
    args = parser.parse_args()

    results = run(args.force, args.workers)
    failed = write_errors(results)
    methods = Counter(r["gif_method"] for r in results if r["gif_method"])
    print(f"\nConvertiti: {len(results) - failed}/{len(results)} | con errori: {failed} (vedi {config.ERRORS_LOG.name})")
    print("Metodi GIF usati:", dict(methods) or "-")
    import verify
    verify.main()


if __name__ == "__main__":
    main()
