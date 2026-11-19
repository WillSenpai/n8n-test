# telegram-emoji-dl

Scarica le **emoji animate classiche di Telegram** (due set ufficiali) e le converte in formati
utilizzabili: `.tgs` → `.json` (Lottie), `.gif` trasparente 512×512, `.png` del primo frame.

## 1. Ottenere `api_id` e `api_hash`

1. Vai su <https://my.telegram.org> e accedi con il tuo numero di telefono.
2. Apri **API development tools**.
3. Crea una nuova applicazione (nome e short name a piacere, es. "emoji-dl").
4. Copia **App api_id** e **App api_hash**.

Non condividerli e non committarli: restano solo nel tuo file `.env` (già ignorato da git).

## 2. Installazione

Richiede Python 3.10+ (ffmpeg è opzionale, serve solo come metodo di ripiego per le GIF).

```bash
cd telegram-emoji-dl
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # poi modifica .env con i tuoi valori
```

Contenuto di `.env`:

```
TG_API_ID=123456
TG_API_HASH=0123456789abcdef0123456789abcdef
```

> La conversione in GIF/PNG usa `cairosvg`, che richiede la libreria di sistema **Cairo**
> (macOS: `brew install cairo`; Debian/Ubuntu: `sudo apt install libcairo2`).
> Per un metodo GIF alternativo puoi installare `pip install rlottie-python`.

## 3. Uso

### Download

```bash
python download.py
```

Al **primo avvio** Telethon ti chiede numero di telefono e codice ricevuto su Telegram
(ed eventualmente la password 2FA); la sessione viene salvata in `telegram_emoji.session`
e dai lanci successivi non serve più. Il file della sessione è ignorato da git: non condividerlo.

Lo script scarica i set `AnimatedEmoji` e `AnimatedEmojiAnimations`, salta i file già presenti
(puoi rilanciarlo senza problemi), gestisce i `FloodWaitError` aspettando il tempo richiesto e
scrive `output/index.json`.

### Conversione e verifica

```bash
python convert.py            # converte tutto, poi stampa la verifica
python convert.py --force    # rigenera anche i file già convertiti
python verify.py             # solo verifica
```

- Per ogni `.tgs` genera `.json`, `.gif` (512×512, sfondo trasparente) e `.png` (primo frame).
- Per la GIF prova in ordine: **lottie** → **rlottie-python** → **ffmpeg** (codifica con palette trasparente)
  e a fine lavoro indica quale metodo ha funzionato.
- Gli errori vanno in `errors.log` e la conversione continua con gli altri file.
- La verifica controlla file vuoti, validità gzip dei `.tgs` e apre 3 GIF a campione (dimensioni e frame).

## 4. Struttura delle cartelle

```
telegram-emoji-dl/
├── config.py  download.py  convert.py  verify.py
├── requirements.txt  .env.example  .gitignore
├── errors.log                      # errori di conversione
└── output/
    ├── index.json                  # file, emoji, set, id documento
    ├── tgs/{animated_emoji,animations}/   # originali .tgs
    ├── json/{animated_emoji,animations}/  # Lottie
    ├── gif/{animated_emoji,animations}/   # GIF 512x512 trasparenti
    └── png/{animated_emoji,animations}/   # primo frame
```

I file sono nominati con l'emoji associata (es. `😀.tgs`); se manca, con un indice a 3 cifre (`001.tgs`);
emoji duplicate nello stesso set ricevono un suffisso (`😀_2.tgs`).

## Nota sui diritti

Le animazioni appartengono a Telegram e ai loro autori. Questo strumento è pensato per **uso personale**.
Per qualsiasi **uso commerciale** verifica prima i diritti e le licenze applicabili.
