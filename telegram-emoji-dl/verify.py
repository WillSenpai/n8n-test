"""Verifica finale: riepilogo per set, file vuoti, validità dei .tgs e controllo a campione delle GIF."""
import gzip
import random
import sys
from pathlib import Path

from PIL import Image

import config


def count(folder: Path, set_name: str, ext: str) -> int:
    """Conta i file con una certa estensione in output/<formato>/<set>."""
    return len(list((folder / set_name).glob(f"*{ext}")))


def error_count() -> int:
    """Numero di righe in errors.log (0 se il file non esiste)."""
    if not config.ERRORS_LOG.exists():
        return 0
    return sum(1 for line in config.ERRORS_LOG.read_text(encoding="utf-8").splitlines() if line.strip())


def empty_files() -> list[Path]:
    """File da 0 byte in tutta la cartella output."""
    return [p for p in config.OUTPUT_DIR.rglob("*") if p.is_file() and p.stat().st_size == 0]


def invalid_tgs() -> list[Path]:
    """File .tgs che non sono gzip validi (letti per intero)."""
    bad = []
    for path in config.TGS_DIR.glob("*/*.tgs"):
        try:
            with gzip.open(path, "rb") as handle:
                while handle.read(1 << 20):
                    pass
        except (OSError, EOFError):
            bad.append(path)
    return bad


def sample_gifs(n: int = 3) -> list[str]:
    """Apre n GIF a caso e riporta dimensioni e numero di frame. Restituisce i problemi trovati."""
    gifs = list(config.GIF_DIR.glob("*/*.gif"))
    problems = []
    for path in random.sample(gifs, min(n, len(gifs))):
        with Image.open(path) as img:
            frames = getattr(img, "n_frames", 1)
            ok = img.size == (config.SIZE, config.SIZE) and frames > 1
            print(f"  GIF {path.parent.name}/{path.name}: {img.size[0]}x{img.size[1]}, {frames} frame -> {'OK' if ok else 'ANOMALIA'}")
            if not ok:
                problems.append(str(path))
    return problems


def print_summary() -> None:
    """Tabella: .tgs scaricati e file convertiti per set."""
    print(f"{'set':<16}{'tgs':>6}{'json':>6}{'gif':>6}{'png':>6}")
    for name in config.SET_NAMES:
        print(f"{name:<16}{count(config.TGS_DIR, name, '.tgs'):>6}{count(config.JSON_DIR, name, '.json'):>6}"
              f"{count(config.GIF_DIR, name, '.gif'):>6}{count(config.PNG_DIR, name, '.png'):>6}")
    print(f"Errori in {config.ERRORS_LOG.name}: {error_count()}")


def main() -> int:
    print("\n=== Verifica ===")
    print_summary()
    empty, bad = empty_files(), invalid_tgs()
    print(f"File vuoti (0 byte): {len(empty)}" + "".join(f"\n  {p}" for p in empty))
    print(f".tgs non validi (gzip): {len(bad)}" + "".join(f"\n  {p}" for p in bad))
    print("Controllo a campione di 3 GIF:")
    problems = sample_gifs()
    return 1 if (empty or bad or problems) else 0


if __name__ == "__main__":
    sys.exit(main())
