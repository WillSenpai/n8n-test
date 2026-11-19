// Librerie di terze parti, installate come dipendenze npm e compilate in locale (nessuna CDN).
// Le espone come globali per la composizione, come farebbe un <script> da CDN.
import gsap from 'gsap';
import lottie from 'lottie-web';

Object.assign(window, {gsap, lottie});
