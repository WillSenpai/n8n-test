"""Configurazione condivisa: percorsi di output e nomi dei set di emoji."""
from pathlib import Path

# Cartella del progetto (dove si trova questo file)
BASE_DIR = Path(__file__).resolve().parent

# Cartelle di output
OUTPUT_DIR = BASE_DIR / "output"
TGS_DIR = OUTPUT_DIR / "tgs"
JSON_DIR = OUTPUT_DIR / "json"
GIF_DIR = OUTPUT_DIR / "gif"
PNG_DIR = OUTPUT_DIR / "png"

# File di supporto
INDEX_FILE = OUTPUT_DIR / "index.json"
ERRORS_LOG = BASE_DIR / "errors.log"
SESSION_FILE = BASE_DIR / "telegram_emoji"  # Telethon aggiunge ".session"

# Nomi (= sottocartelle) dei due set ufficiali di emoji animate
SET_NAMES = ("animated_emoji", "animations")

# Dimensione di GIF e PNG in pixel
SIZE = 512
