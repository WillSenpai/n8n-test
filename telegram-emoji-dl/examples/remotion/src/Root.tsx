import {getLottieMetadata} from '@remotion/lottie';
import {CalculateMetadataFunction, Composition} from 'remotion';
import {EmojiProps, EmojiScene} from './EmojiScene';
import {findEntry, loadLottie, loadManifest} from './manifest';

// Tolleranza per il confronto degli fps (il Lottie può avere fps non interi)
const FPS_TOLERANCE = 0.01;

// Legge fps e durata dal manifest e verifica che coincidano con quelli del Lottie
const calculateMetadata: CalculateMetadataFunction<EmojiProps> = async ({props}) => {
  const entry = findEntry(await loadManifest(), props.set, props.emojiId);
  const animationData = await loadLottie(entry);

  const lottie = getLottieMetadata(animationData);
  if (!lottie) throw new Error(`Lottie non valido: ${entry.file}`);
  const sameFps = Math.abs(lottie.fps - entry.fps) < FPS_TOLERANCE;
  const sameFrames = Math.round(lottie.durationInFrames) === entry.durationInFrames;
  if (!sameFps || !sameFrames) {
    throw new Error(
      `Manifest e Lottie non coincidono per ${entry.file}: ` +
        `manifest ${entry.fps}fps/${entry.durationInFrames}f, lottie ${lottie.fps}fps/${lottie.durationInFrames}f`,
    );
  }
  return {fps: entry.fps, durationInFrames: entry.durationInFrames, props: {...props, animationData}};
};

export const Root: React.FC = () => (
  <Composition
    id="Emoji"
    component={EmojiScene}
    width={1920}
    height={1080}
    fps={60}
    durationInFrames={120} // valori provvisori: li sovrascrive calculateMetadata
    defaultProps={{set: 'animated_emoji', emojiId: '1f600', animationData: null}}
    calculateMetadata={calculateMetadata}
  />
);
