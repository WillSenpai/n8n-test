#!/usr/bin/env bash
# Installa tutto: ambiente Python, dipendenze Node (strumenti + due esempi) e Chromium per i test.
# Uso: ./setup.sh   (su Windows usa Git Bash o WSL)
set -euo pipefail
cd "$(dirname "$0")"

echo "==> Python: virtualenv e dipendenze"
python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt

echo "==> Node: strumenti (lottie-web, playwright) e due esempi"
npm install --no-audit --no-fund
(cd examples/remotion && npm install --no-audit --no-fund)
(cd examples/hyperframes && npm install --no-audit --no-fund)

echo "==> Chromium per il test di compatibilità (se già presente puoi saltarlo con Ctrl+C)"
npx playwright install chromium || echo "Installazione Chromium non riuscita: imposta CHROME_PATH a un Chrome esistente."

[ -f .env ] || { cp .env.example .env; echo "==> Creato .env: inserisci TG_API_ID e TG_API_HASH"; }
echo "Fatto. Prossimo passo: ./run_all.sh (al primo avvio Telegram chiede numero e codice)"
