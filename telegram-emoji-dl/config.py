"""Configurazione condivisa: percorsi e nomi dei set di emoji."""
from pathlib import Path

# Cartella del progetto (dove si trova questo file)
BASE_DIR = Path(__file__).resolve().parent

# Originali .tgs scaricati da Telegram (ignorati da git)
OUTPUT_DIR = BASE_DIR / "output"
TGS_DIR = OUTPUT_DIR / "tgs"
INDEX_FILE = OUTPUT_DIR / "index.json"

# Asset finali pronti per Remotion/HyperFrames (JSON Lottie + manifest)
LOTTIE_DIR = BASE_DIR / "public" / "lottie"
MANIFEST_FILE = LOTTIE_DIR / "manifest.json"

# Report e log
REPORTS_DIR = BASE_DIR / "reports"
COMPAT_REPORT = BASE_DIR / "compat-report.json"
ERRORS_LOG = BASE_DIR / "errors.log"

# File di sessione Telethon (Telethon aggiunge ".session")
SESSION_FILE = BASE_DIR / "telegram_emoji"

# Sottocartelle (= nomi) dei due set ufficiali di emoji animate
SET_NAMES = ("animated_emoji", "animations")

# Campi obbligatori in un Lottie: fps, frame iniziale, frame finale, larghezza, altezza
LOTTIE_REQUIRED = ("fr", "ip", "op", "w", "h")
