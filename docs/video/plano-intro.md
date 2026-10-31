# Intro do vídeo de demo (30 s)

O manual do hackathon pede um vídeo de demo de até 5 minutos, entregue até 13h de 31/10.
Esta intro abre o vídeo. O resto (demo da plataforma) é editado depois.

## Decisões (31/10)

- Estilo voxel/pixel 3D, feito no Blender por código. Combina com o site e com a logo pixelada.
- Música original composta por código: piano, celesta e marimba, 96 BPM, sem direitos autorais.
- Logo e slogan aparecem no próprio quadro negro, sem corte até o final.
- Narração do slogan: alguém do time grava depois. Por enquanto, sem voz.
- Cores de `web/css/tokens.css`; logo recriada a partir de `web/assets/img/prisma-logo.svg`.
- Fontes: Pixelify Sans para títulos e Atkinson Hyperlegible Next para o slogan.

## Linha do tempo

96 BPM: um compasso a cada 2,5 s. Cada evento cai no início de um compasso.

| Tempo | Imagem | Som |
|---|---|---|
| 0 a 2,5 s | A tela clareia. Plano aberto do fundo da sala, luz da manhã. A professora aponta o PRISMA de giz com o ponteiro | fundo suave e celesta |
| 2,5 a 7,5 s | A porta abre e a aluna cadeirante entra. A professora acena e a turma sorri. Ela vai para o lugar dela na primeira fila | entra o piano |
| 7,5 a 17,5 s | Sobrevoo pelas carteiras. Palavras aparecem a cada 1,25 s, sobem e somem. A professora anda até a frente do quadro e conversa com a turma; alunos levantam a mão, cochicham, escrevem e balançam a cabeça no ritmo | marimba, uma nota por palavra |
| 17,5 a 20 s | A câmera chega ao quadro enquanto a professora aponta o "PRISMA" a giz | a música cresce |
| 20 a 22,5 s | O giz vira pó e o prisma pixelado se monta bloco a bloco | acorde suspenso |
| 22,5 a 25 s | O raio branco entra pela esquerda e as 6 cores saem uma a uma | sopro suave e arpejo de 6 notas |
| 25 a 29,5 s | Slogan: "PRISMA: uma aula entra, várias versões saem." A câmera recua e mostra a professora apontando a logo | acorde final |
| 29,5 a 30 s | Corte seco para preto | whoosh de vento |

Palavras: inclusão, acessibilidade, aprender, ver, ouvir, ler, autonomia, para todos. Sem placa de fundo, só uma sombra fina escura para ler sobre a parede clara.

Ajustes de 31/10 (madrugada): mais movimento na sala (ventiladores de teto girando, turma se mexendo), professora com ponteiro e caminhada, palavras sem placa preta. Render final em 32 amostras, por tempo.

## Acessibilidade do vídeo

- Nada pisca: a luz acende em rampa suave (WCAG 2.3.1, no máximo 3 clarões por segundo).
- Cada texto fica pelo menos 2 a 3 s na tela, com alto contraste.
- Volume moderado e whoosh com pico limitado.
- Turma diversa: aluno de óculos, aluna com aparelho auditivo, aluna cadeirante com mesa na altura certa.

## Etapas

1. Cenário e personagens no Blender.
2. Quadros de checagem para aprovação.
3. Prévia com música (metade da resolução).
4. Ajustes.
5. Render final em Full HD. Saem o MP4 e o WAV da trilha separado.
