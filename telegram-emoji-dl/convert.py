"""Converte i .tgs in JSON Lottie (public/lottie/<set>/) e genera manifest.json."""
import gzip
import json
import re
from datetime import datetime
from pathlib import Path

import config

VARIATION_SELECTOR = 0xFE0F  # selettore di variazione emoji: ignorato nello slug


def slug_from_emoji(emoji: str) -> str:
    """Nome file ASCII dai codepoint dell'emoji (es. 😀 -> 1f600), sicuro per URL e path locali."""
    points = [f"{ord(c):x}" for c in emoji if ord(c) != VARIATION_SELECTOR]
    return "-".join(points)


def load_index() -> dict[str, dict]:
    """Legge output/index.json (file -> voce). Vuoto se non esiste."""
    if not config.INDEX_FILE.exists():
        return {}
    entries = json.loads(config.INDEX_FILE.read_text(encoding="utf-8"))
    return {e["file"]: e for e in entries}


def guess_emoji(stem: str) -> str:
    """Senza index.json: l'emoji è il nome file se non è ASCII (tolto il suffisso _2, _3...)."""
    base = re.sub(r"_\d+$", "", stem)
    return base if base and not base.isascii() else ""


def list_tgs() -> list[Path]:
    """Elenca i .tgs in ordine stabile (set, poi nome)."""
    return sorted(config.TGS_DIR.glob("*/*.tgs"))


def read_tgs(path: Path) -> dict:
    """Gunzip + parsing JSON. Solleva eccezione se non è un gzip/JSON valido."""
    with gzip.open(path, "rb") as handle:
        return json.loads(handle.read())


def validate_lottie(data: dict) -> None:
    """Controlla che ci siano fr, ip, op, w, h numerici e che fps e dimensioni siano sensati."""
    missing = [k for k in config.LOTTIE_REQUIRED if k not in data]
    if missing:
        raise ValueError(f"campi mancanti: {', '.join(missing)}")
    if any(not isinstance(data[k], (int, float)) for k in config.LOTTIE_REQUIRED):
        raise ValueError("i campi fr/ip/op/w/h devono essere numerici")
    if data["fr"] <= 0 or data["op"] <= data["ip"] or data["w"] <= 0 or data["h"] <= 0:
        raise ValueError("valori non validi (fr, ip/op o dimensioni)")


def unique_slug(slug: str, used: set[str]) -> str:
    """Evita collisioni di nome nello stesso set aggiungendo _2, _3..."""
    final, n = slug, 1
    while final in used:
        n += 1
        final = f"{slug}_{n}"
    used.add(final)
    return final


def manifest_entry(set_name: str, slug: str, emoji: str, data: dict, doc_id) -> dict:
    """Voce del manifest: durata in frame e secondi derivate da fr/ip/op."""
    frames = round(data["op"] - data["ip"])
    return {
        "id": slug,
        "file": f"{set_name}/{slug}.json",
        "emoji": emoji,
        "set": set_name,
        "fps": data["fr"],
        "durationInFrames": frames,
        "durationInSeconds": round(frames / data["fr"], 3),
        "width": data["w"],
        "height": data["h"],
        "documentId": doc_id,
    }


def convert_one(path: Path, index: dict, used: dict[str, set[str]]) -> dict:
    """Converte un .tgs: scrive il JSON e restituisce la voce di manifest."""
    set_name = path.parent.name
    meta = index.get(f"{set_name}/{path.name}", {})
    emoji = meta.get("emoji") or guess_emoji(path.stem)
    data = read_tgs(path)
    validate_lottie(data)
    slug = unique_slug(slug_from_emoji(emoji) or path.stem, used.setdefault(set_name, set()))
    dest = config.LOTTIE_DIR / set_name / f"{slug}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return manifest_entry(set_name, slug, emoji, data, meta.get("document_id"))


def write_errors(errors: list[str]) -> None:
    """Scrive errors.log (sovrascrive: ogni run riparte da zero)."""
    config.ERRORS_LOG.write_text("\n".join(errors) + ("\n" if errors else ""), encoding="utf-8")


def main() -> None:
    files = list_tgs()
    if not files:
        raise SystemExit(f"Nessun .tgs in {config.TGS_DIR}: lancia prima download.py")
    index, used = load_index(), {}
    manifest, errors = [], []
    for path in files:
        try:
            manifest.append(convert_one(path, index, used))
        except Exception as err:  # noqa: BLE001 - un file corrotto non deve fermare gli altri
            errors.append(f"{datetime.now():%Y-%m-%d %H:%M:%S}\t{path.parent.name}/{path.name}\t{type(err).__name__}: {err}")
    manifest.sort(key=lambda e: (e["set"], e["id"]))
    config.MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.MANIFEST_FILE.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    write_errors(errors)
    print(f"Convertiti {len(manifest)}/{len(files)} | errori: {len(errors)} (vedi {config.ERRORS_LOG.name})")
    print(f"Manifest: {config.MANIFEST_FILE}")


if __name__ == "__main__":
    main()
