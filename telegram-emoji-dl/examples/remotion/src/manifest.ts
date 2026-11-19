import {staticFile} from 'remotion';

// Voce di public/lottie/manifest.json (generato da convert.py)
export type ManifestEntry = {
  id: string;
  file: string; // es. "animated_emoji/1f600.json" (relativo a public/lottie)
  emoji: string;
  set: string;
  fps: number;
  durationInFrames: number;
  durationInSeconds: number;
  width: number;
  height: number;
};

// Legge il manifest con staticFile() (file locale in public/lottie)
export const loadManifest = async (): Promise<ManifestEntry[]> => {
  const res = await fetch(staticFile('lottie/manifest.json'));
  if (!res.ok) throw new Error('manifest.json non trovato: lancia convert.py');
  return res.json();
};

// Cerca un'emoji per id (es. "1f600") dentro un set
export const findEntry = (manifest: ManifestEntry[], set: string, id: string): ManifestEntry => {
  const entry = manifest.find((e) => e.set === set && e.id === id);
  if (!entry) throw new Error(`Emoji "${id}" non presente nel set "${set}" del manifest`);
  return entry;
};

// Carica il Lottie JSON di una voce del manifest con staticFile()
export const loadLottie = async (entry: ManifestEntry) => {
  const res = await fetch(staticFile(`lottie/${entry.file}`));
  if (!res.ok) throw new Error(`Impossibile caricare ${entry.file}`);
  return res.json();
};
