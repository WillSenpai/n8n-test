"""Verifica finale: riepilogo (tgs, JSON, compatibilità, render) e controlli di integrità."""
import gzip
import json
import sys
from pathlib import Path

import config


def count_files(folder: Path, pattern: str) -> dict[str, int]:
    """Conta i file per set (sottocartella) con un certo pattern."""
    return {name: len(list((folder / name).glob(pattern))) for name in config.SET_NAMES}


def read_json(path: Path):
    """Legge un JSON se esiste, altrimenti None."""
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def empty_files() -> list[Path]:
    """File da 0 byte in output/ e public/lottie/."""
    found = []
    for folder in (config.OUTPUT_DIR, config.LOTTIE_DIR):
        found += [p for p in folder.rglob("*") if p.is_file() and p.stat().st_size == 0]
    return found


def invalid_tgs() -> list[Path]:
    """File .tgs che non sono un gzip valido (letti per intero)."""
    bad = []
    for path in config.TGS_DIR.glob("*/*.tgs"):
        try:
            with gzip.open(path, "rb") as handle:
                while handle.read(1 << 20):
                    pass
        except (OSError, EOFError):
            bad.append(path)
    return bad


def error_lines() -> list[str]:
    """Righe presenti in errors.log."""
    if not config.ERRORS_LOG.exists():
        return []
    return [line for line in config.ERRORS_LOG.read_text(encoding="utf-8").splitlines() if line.strip()]


def print_counts() -> None:
    """Tabella: .tgs scaricati e JSON convertiti per set."""
    tgs, jsons = count_files(config.TGS_DIR, "*.tgs"), count_files(config.LOTTIE_DIR, "*.json")
    print(f"{'set':<18}{'.tgs':>6}{'json':>6}")
    for name in config.SET_NAMES:
        print(f"{name:<18}{tgs[name]:>6}{jsons[name]:>6}")
    print(f"{'totale':<18}{sum(tgs.values()):>6}{sum(jsons.values()):>6}")


def print_compat() -> None:
    """Esito del test lottie-web (compat-report.json)."""
    report = read_json(config.COMPAT_REPORT)
    if not report:
        print("Compatibilità lottie-web: non eseguita (npm run compat)")
        return
    print(f"Compatibilità lottie-web: {report['okCount']} OK, {report['failedCount']} problematici")
    for item in report["failed"]:
        print(f"  ✗ {item['file']}: {item['cause']}")


def print_renders() -> bool:
    """Esito dei render di prova. Restituisce False se uno è fallito."""
    all_ok = True
    for target in ("remotion", "hyperframes"):
        report = read_json(config.REPORTS_DIR / f"render-{target}.json")
        if not report:
            print(f"Render {target}: non eseguito (npm run test:{target})")
        elif report["ok"]:
            print(f"Render {target}: OK ({report['emoji']}, emoji visibile)")
        else:
            all_ok = False
            print(f"Render {target}: FALLITO - {report.get('error', 'emoji non visibile')[:300]}")
    return all_ok


def main() -> int:
    print("=== Riepilogo ===")
    print_counts()
    errors = error_lines()
    print(f"Errori di conversione (errors.log): {len(errors)}")
    print_compat()
    renders_ok = print_renders()

    print("\n=== Integrità ===")
    empty, bad = empty_files(), invalid_tgs()
    print(f"File vuoti (0 byte): {len(empty)}" + "".join(f"\n  {p}" for p in empty))
    print(f".tgs non gzip validi: {len(bad)}" + "".join(f"\n  {p}" for p in bad))
    return 0 if not (empty or bad or errors) and renders_ok else 1


if __name__ == "__main__":
    sys.exit(main())
