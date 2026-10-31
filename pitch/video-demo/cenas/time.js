/* Dinâmica "Nós somos a PRISMA" (bloco 2).
   Cada cartão mostra um vídeo de ../gravacoes/time-N.mp4 (feito pelo recortar.py a partir de whats-N.mp4).
   palavra: o que a pessoa fala (aparece no cartão e na legenda).
   fala: segundo do vídeo original em que a palavra começa (medido no áudio). */
window.TIME = [
  { palavra: "nós", fala: 3.0 },
  { palavra: "somos", fala: 2.5 },
  { palavra: "a", fala: 3.15 },
  { palavra: "PRISMA", fala: 2.4 }
];
/* cartoes: quando cada cartão acende; a palavra vem ANTES_FALA segundos depois. */
window.TEMPOS_TIME = { cartoes: [0.2, 1.2, 2.2, 3.2], antes_fala: 0.6, logo: 5.0, fim: 8.8 };
