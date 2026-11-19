// Composizione HyperFrames: mostra un Lottie (emoji animata) con lottie-web, controllato SOLO tramite seek.
// Regole rispettate: file solo locali, autoplay/loop disattivati, niente play(), contenitore a dimensioni fisse (CSS).
// gsap e lottie sono globali caricati da vendor/libs.min.js (compilato da src/libs.ts), non importati qui.
import type {AnimationItem, AnimationConfigWithPath, LottiePlayer} from 'lottie-web';

declare const lottie: LottiePlayer;
declare const gsap: {
  timeline(vars?: object): {to(target: object, vars: object, position?: number): unknown};
};

declare global {
  interface Window {
    __hfLottie?: AnimationItem[]; // player che il runtime HyperFrames porta al tempo corretto (seek)
    __timelines?: Record<string, unknown>;
    __hyperframes?: {assetUrl?: (path: string) => string};
  }
}

const COMPOSITION_ID = 'emoji';
const LOTTIE_FILE = 'assets/emoji.json'; // copiato in locale da scripts/prepare.mjs

// Percorso locale dell'asset (se il runtime lo espone usa assetUrl, altrimenti il path relativo)
const assetUrl = (path: string): string => window.__hyperframes?.assetUrl?.(path) ?? path;

// Il player Lottie: SVG, niente autoplay, niente loop
const createPlayer = (container: HTMLElement): AnimationItem =>
  lottie.loadAnimation({
    container,
    renderer: 'svg',
    loop: false,
    autoplay: false,
    path: assetUrl(LOTTIE_FILE),
  });

// Timeline GSAP in pausa, lunga quanto la composizione: serve al runtime per registrare la durata
const createTimeline = (durationSeconds: number) => {
  const timeline = gsap.timeline({paused: true});
  timeline.to({}, {duration: durationSeconds}, 0);
  return timeline;
};

const root = document.getElementById('root')!; // elemento con data-composition-id="emoji"
const container = document.getElementById('emoji')!;

const player = createPlayer(container);
(window.__hfLottie ??= []).push(player);

window.__timelines ??= {};
window.__timelines[COMPOSITION_ID] = createTimeline(Number(root.dataset.duration));
