#!/usr/bin/env bash
# Esegue tutta la pipeline: download -> conversione -> test lottie-web -> render di prova -> verifica.
# Uso: ./run_all.sh
set -uo pipefail
cd "$(dirname "$0")"

.venv/bin/python download.py || exit 1     # al primo avvio chiede numero di telefono e codice
.venv/bin/python convert.py || exit 1
npm run --silent compat
npm run --silent test:remotion
npm run --silent test:hyperframes
.venv/bin/python verify.py
