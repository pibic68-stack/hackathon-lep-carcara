# Intro do vídeo (30 s)

Sala de aula voxel no Blender: a aluna cadeirante entra, as palavras flutuam pela sala, a câmera chega ao quadro, o giz vira o prisma da logo, o raio de luz abre as seis cores e aparece o slogan.
O plano está em `docs/video/plano-intro.md`.

## Arquivos

| Arquivo | O que faz |
|---|---|
| `cena.py` | Apaga a cena e monta tudo: sala, turma, professora, aluna, quadro, logo em pixels, palavras, luzes |
| `animacao.py` | Grava os keyframes e escreve `saida/eventos.json` com os tempos de cada evento |
| `trilha.py` | Compõe a música e os efeitos com numpy (96 BPM) a partir de `eventos.json` |
| `montar.py` | Junta os quadros e a trilha num MP4 |
| `checar.py`, `quadros.py` | Renders de checagem |

A pasta `saida/` fica fora do Git: `.blend`, quadros, trilha, MP4 e as fontes convertidas para TTF.

## Como refazer

1. Abra o Blender 5.2 com o add-on MCP e rode `cena.py` e depois `animacao.py` (pelo Claude ou pelo editor de texto do Blender).
2. Converta as fontes do site para TTF em `saida/fontes/`: pixelify-700 e atkinson-700, com `fontTools`.
3. Renderize a animação (quadros 1 a 708) em `saida/previa/` ou `saida/final/`.
4. Rode `python trilha.py` e depois `python montar.py previa` (ou `final`).

## Sincronia

Cada compasso dura 2,5 s. A porta abre em 2,5 s e cada palavra entra a cada 1,25 s, com uma nota de marimba.
O quadro começa em 20 s. O raio entra em 22,5 s e as cores saem uma por colcheia (0,3125 s), cada uma com sua nota.
O slogan entra em 25 s, com o acorde final. O corte com o whoosh vem em 29,5 s.
Para mudar um tempo, edite `animacao.py`, rode de novo e refaça a trilha.

## Acessibilidade

- Nada pisca: a luz acende em rampa (WCAG 2.3.1).
- Os textos ficam no mínimo 2 s na tela. As palavras flutuantes têm uma sombra fina escura em vez de placa, para continuarem legíveis sobre a parede clara.
- O volume é moderado: média de −19 dBFS e pico de −1,5 dBFS.
- A narração do slogan entra depois: há espaço livre de 25 s a 29,5 s.
