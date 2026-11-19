# telegram-emoji-dl

Scarica **tutte le emoji animate classiche di Telegram** e le prepara per essere usate in
**[Remotion](https://www.remotion.dev)** e **[HyperFrames](https://github.com/heygen-com/hyperframes)**
come **Lottie JSON vettoriali**.

## A cosa serve

Le emoji animate di Telegram sono file `.tgs` (Lottie compresso). Per il video editing a 1080p o 4K le GIF/PNG
non vanno bene (512 px, 256 colori). I Lottie invece sono vettoriali: restano nitidi a qualsiasi risoluzione,
si possono ridimensionare, posizionare e sincronizzare frame per frame nei video generati da codice.

Il progetto automatizza tutto:

1. scarica i due set ufficiali di emoji animate da Telegram (`.tgs`);
2. li converte in JSON Lottie in `public/lottie/` con un `manifest.json` (fps, durata, dimensioni);
3. verifica la compatibilità con **lottie-web** (il motore usato da HyperFrames);
4. include un esempio minimo per Remotion e uno per HyperFrames, con render di prova automatici.

> I `.tgs` si scaricano con **il tuo account Telegram** (serve il login una volta), quindi gli asset non sono
> inclusi nel repo finché non lanci la pipeline. Dopo averla lanciata, committa `public/lottie/`: da quel momento
> chiunque clona il repo (o scarica quella cartella) ha subito tutto il necessario senza login.

## Avvio rapido

```bash
./setup.sh       # installa Python + Node + Chromium
# apri .env e inserisci TG_API_ID e TG_API_HASH (vedi sotto)
./run_all.sh     # download -> conversione -> test -> render di prova -> verifica
```

Requisiti: Python 3.10+, Node 22+, ffmpeg. (Su Windows usa Git Bash o WSL, oppure lancia i comandi a mano.)

## Come ottenere `api_id` e `api_hash`

1. Vai su <https://my.telegram.org> e accedi con il tuo numero.
2. Apri **API development tools** e crea un'applicazione (nome e short name a piacere).
3. Copia **api_id** e **api_hash** nel file `.env` (copia di `.env.example`):

```
TG_API_ID=123456
TG_API_HASH=0123456789abcdef0123456789abcdef
```

`.env` e `*.session` sono nel `.gitignore`: non committarli e non condividerli.

## Installazione manuale

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
npm install
(cd examples/remotion && npm install)
(cd examples/hyperframes && npm install)
npx playwright install chromium
```

## Come lanciare ogni script

| Comando | Cosa fa |
|---|---|
| `python download.py` | Scarica i `.tgs` in `output/tgs/<set>/` e scrive `output/index.json`. Al primo avvio chiede numero di telefono e codice; la sessione resta in `telegram_emoji.session`. Si può rilanciare: salta i file già scaricati e aspetta i `FloodWait`. |
| `python convert.py` | `.tgs` → JSON in `public/lottie/<set>/`, valida `fr, ip, op, w, h`, genera `manifest.json`. I file corrotti vanno in `errors.log`. |
| `npm run preview` | Anteprima nel browser: griglia animata di tutte le emoji con ricerca (`npm run preview -- 🚀` o `-- 1f680`), filtro per set, finestra di dettaglio con play/pausa e seek frame per frame. |
| `npm run compat` | Carica ogni JSON in lottie-web (headless Chrome), fa seek su inizio/metà/fine e scrive `compat-report.json`. |
| `npm run test:remotion` | Render di 1 frame dell'esempio Remotion e controllo che l'emoji compaia. |
| `npm run test:hyperframes` | Render MP4 dell'esempio HyperFrames e stesso controllo. |
| `python verify.py` | Riepilogo finale: file per set, compatibilità, esito dei render, file vuoti, gzip validi. |

Se Chrome non viene trovato imposta `CHROME_PATH=/percorso/di/chrome`.

## Struttura delle cartelle

```
telegram-emoji-dl/
├── download.py  convert.py  verify.py  config.py     # pipeline Python
├── setup.sh  run_all.sh  requirements.txt  .env.example
├── package.json  compat/  scripts/  preview/         # test lottie-web, render di prova, anteprima nel browser
├── public/lottie/                                    # ASSET FINALI (da committare)
│   ├── manifest.json
│   ├── animated_emoji/*.json
│   └── animations/*.json
├── examples/
│   ├── remotion/                                     # composizione TypeScript con @remotion/lottie
│   └── hyperframes/                                  # composizione HTML + TypeScript con lottie-web
├── output/tgs/{animated_emoji,animations}/           # .tgs originali (ignorati da git)
├── compat-report.json  reports/  errors.log          # esiti e log (generati)
```

I file JSON hanno nome **ASCII** dai codepoint Unicode (😀 → `1f600.json`, 👨‍💻 → `1f468-200d-1f4bb.json`) per evitare
problemi con URL e percorsi; l'emoji vera è nel `manifest.json`. I `.tgs` originali mantengono come nome l'emoji
(o un indice a 3 cifre se manca).

### Formato di `manifest.json`

```json
{ "id": "1f600", "file": "animated_emoji/1f600.json", "emoji": "😀", "set": "animated_emoji",
  "fps": 60, "durationInFrames": 120, "durationInSeconds": 2, "width": 512, "height": 512, "documentId": 123 }
```

## Anteprima nel browser

Dopo `convert.py`:

```bash
npm run preview            # griglia di tutte le emoji
npm run preview -- 🚀      # apre già filtrata (anche per id: 1f680)
```

Apri l'indirizzo stampato (`http://127.0.0.1:5173`). Le animazioni partono solo quando la card è visibile, quindi resta
fluida anche con centinaia di emoji. L'anteprima fa girare i Lottie in loop: serve per guardarli, non per montare i video
(per quello usa gli esempi Remotion/HyperFrames).

## Usare un'emoji in Remotion

Copia i JSON in `public/lottie/` del tuo progetto (o usa `Config.setPublicDir`), poi:

```tsx
import {Lottie, LottieAnimationData} from '@remotion/lottie';
import {useEffect, useState} from 'react';
import {cancelRender, continueRender, delayRender, staticFile} from 'remotion';

export const Emoji: React.FC<{file: string}> = ({file}) => {
  const [handle] = useState(() => delayRender('Lottie'));
  const [data, setData] = useState<LottieAnimationData | null>(null);

  useEffect(() => {
    fetch(staticFile(`lottie/${file}`)) // es. "animated_emoji/1f600.json"
      .then((r) => r.json())
      .then((json) => { setData(json); continueRender(handle); })
      .catch(cancelRender);
  }, [file, handle]);

  return data ? <Lottie animationData={data} style={{width: 800, height: 800}} /> : null;
};
```

L'esempio completo (`examples/remotion`) legge `fps` e durata dal manifest tramite `calculateMetadata` e verifica che
coincidano con quelli del Lottie (`getLottieMetadata`). Prova: `cd examples/remotion && npm run dev`.

## Usare un'emoji in HyperFrames

Regole: **file solo locali** (mai URL), **niente `play()`**, `autoplay` e `loop` disattivati, contenitore con
**dimensioni fisse in CSS**. Il player va registrato in `window.__hfLottie`: HyperFrames lo porta al frame giusto con il seek.

```html
<div id="root" data-composition-id="emoji" data-start="0" data-duration="2" data-fps="60"
     data-width="1920" data-height="1080">
  <div id="emoji" style="position:absolute; left:560px; top:140px; width:800px; height:800px"></div>
</div>
<script src="vendor/libs.min.js"></script> <!-- lottie-web + gsap da npm, compilati in locale (src/libs.ts) -->
<script>
  const anim = lottie.loadAnimation({
    container: document.getElementById("emoji"),
    renderer: "svg", loop: false, autoplay: false,
    path: "assets/emoji.json",            // copia locale del JSON
  });
  (window.__hfLottie = window.__hfLottie || []).push(anim);
  window.__timelines = window.__timelines || {};
  window.__timelines["emoji"] = gsap.timeline({ paused: true }).to({}, { duration: 2 }); // durata composizione
</script>
```

L'esempio completo (`examples/hyperframes`, TypeScript compilato con esbuild, lottie-web e gsap da npm):

```bash
cd examples/hyperframes
npm run prepare:emoji -- animated_emoji 1f600   # copia il JSON, compila e genera index.html con durata/fps giusti
npx hyperframes lint
npx hyperframes preview
npx hyperframes render -o renders/emoji.mp4     # --format mov per avere lo sfondo trasparente
```

## Limiti noti

- I `.tgs` sono pensati per **rlottie**: alcune animazioni potrebbero renderizzare in modo leggermente diverso su
  lottie-web. `compat-report.json` elenca i file che falliscono o escono vuoti; se un frame è vuoto solo in alcuni
  punti viene segnalato come avviso.
- HyperFrames renderizza a 30 fps se la root non ha `data-fps`: l'esempio lo imposta uguale a quello del Lottie.

## Diritti d'uso

Le animazioni appartengono a Telegram e ai loro autori. Questo strumento è pensato per **uso personale**.
Per **uso commerciale** o per **video pubblicati** verifica prima i diritti e le licenze applicabili.
