import {Lottie, LottieAnimationData} from '@remotion/lottie';
import {AbsoluteFill} from 'remotion';

export type EmojiProps = {
  set: string; // es. "animated_emoji"
  emojiId: string; // es. "1f600" (vedi public/lottie/manifest.json)
  animationData: LottieAnimationData | null; // riempito da calculateMetadata
};

const EMOJI_SIZE = 800; // px, dimensione fissa del contenitore

// Mostra l'emoji al centro su fondo scuro. Il Lottie è vettoriale: resta nitido a qualsiasi risoluzione.
export const EmojiScene: React.FC<EmojiProps> = ({animationData}) => {
  if (!animationData) return null;
  return (
    <AbsoluteFill style={{backgroundColor: '#1b1f3a', justifyContent: 'center', alignItems: 'center'}}>
      <Lottie animationData={animationData} style={{width: EMOJI_SIZE, height: EMOJI_SIZE}} />
    </AbsoluteFill>
  );
};
