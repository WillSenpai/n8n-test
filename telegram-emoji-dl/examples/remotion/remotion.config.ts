import {Config} from '@remotion/cli/config';

// Gli asset (public/lottie) stanno nella radice del progetto, non dentro l'esempio
Config.setPublicDir('../../public');
Config.setVideoImageFormat('png');
