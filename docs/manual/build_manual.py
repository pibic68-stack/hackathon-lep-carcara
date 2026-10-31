#!/usr/bin/env python3
"""Gera o Manual PRISMA (PDF) a partir de padroes.json, a fonte única.

Uso:
    python3 docs/manual/build_manual.py
Saídas:
    docs/manual/manual-prisma-v1.pdf   (para baixar)

Para mudar um padrão, critério, dado ou referência, edite padroes.json e rode de novo.
O texto corrido das partes (introduções, famílias, estudantes) está neste arquivo.
"""
import argparse
import base64
import html
import json
import math
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).parent
D = json.loads((AQUI / "padroes.json").read_text(encoding="utf-8"))
ESC = html.escape
SIMB = {"dados": "●", "pratica": "◆", "norma": "■", "projeto": "○"}
ROT = {"dados": "Dados", "pratica": "Prática", "norma": "Norma", "projeto": "Projeto"}
AUTO = {"automatico": "Automático", "ia_revisao": "IA + revisão", "manual": "Manual"}
INK, MUTED, GRID, BLUE = "#1E2235", "#4A4F6A", "#D9D3C4", "#1F6FB2"  # tokens do site (web/css/tokens.css)
CAT = ["#57B3F9", "#FFAD60", "#7BD389", "#FFC93C", "#B89AF0", "#8A5A2B"]  # as cores do site: céu, laranja, grama, sol, lilás, carcará
ROTULO_FATIA = [INK, INK, INK, INK, INK, "#FFFFFF"]  # cor do número dentro de cada fatia (contraste)


LOGO_SVG = AQUI.parent.parent / "web" / "assets" / "img" / "prisma-logo.svg"
FONTES = AQUI.parent.parent / "web" / "assets" / "fontes"
LOGO = "data:image/svg+xml;base64," + base64.b64encode(LOGO_SVG.read_bytes()).decode()


def br(n, casas=0):
    s = f"{n:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s


# ---------------- gráficos estáticos ----------------
def rosca(fatias, titulo, fonte, nota=""):
    tot = sum(f["valor"] for f in fatias)
    cx, cy, R, r = 150, 150, 130, 78
    s = [f'<svg viewBox="0 0 300 300" class="rosca" role="img" aria-label="{ESC(titulo)}">']
    ang = -math.pi / 2
    for i, f in enumerate(fatias):
        a = 2 * math.pi * f["valor"] / tot
        a0, a1 = ang, ang + a
        g = 0.012  # vão de superfície entre fatias
        a0g, a1g = a0 + g, a1 - g
        large = 1 if a1g - a0g > math.pi else 0
        p = (f"M{cx+R*math.cos(a0g):.2f},{cy+R*math.sin(a0g):.2f} A{R},{R} 0 {large} 1 {cx+R*math.cos(a1g):.2f},{cy+R*math.sin(a1g):.2f} "
             f"L{cx+r*math.cos(a1g):.2f},{cy+r*math.sin(a1g):.2f} A{r},{r} 0 {large} 0 {cx+r*math.cos(a0g):.2f},{cy+r*math.sin(a0g):.2f} Z")
        s.append(f'<path d="{p}" fill="{CAT[i]}" stroke="{INK}" stroke-width="2.5" stroke-linejoin="miter"/>')
        pct = 100 * f["valor"] / tot
        if pct >= 10:
            m = (a0 + a1) / 2
            rm = (R + r) / 2
            s.append(f'<text x="{cx+rm*math.cos(m):.1f}" y="{cy+rm*math.sin(m)+5:.1f}" text-anchor="middle" font-size="15" font-weight="700" fill="{ROTULO_FATIA[i]}">{br(pct)}%</text>')
        ang = a1
    s.append(f'<text x="{cx}" y="{cy-4}" text-anchor="middle" font-size="22" font-weight="700" fill="{INK}">{br(tot/1e6,2)} mi</text>')
    s.append(f'<text x="{cx}" y="{cy+18}" text-anchor="middle" font-size="12" fill="{MUTED}">registros</text></svg>')
    leg = "".join(f'<li><i style="background:{CAT[i]}"></i><span>{ESC(f["nome"])}</span><b>{br(100*f["valor"]/tot,1)}%</b><em>{br(f["valor"])}</em></li>' for i, f in enumerate(fatias))
    return (f'<figure class="fig-rosca"><figcaption class="tit">{ESC(titulo)}</figcaption><div class="rosca-grade">{"".join(s)}'
            f'<ul class="leg-rosca">{leg}</ul></div><figcaption class="fonte">Fonte: {ESC(fonte)}. {ESC(nota)}</figcaption></figure>')


def barras_h(titulo, itens, fonte, maximo=100, sufixo="%", largura=640, esq=190):
    alt_l, topo = 44, 8
    alt = topo + alt_l * len(itens) + 34
    util = largura - esq - 70
    s = [f'<svg viewBox="0 0 {largura} {alt}" class="grafico" role="img" aria-label="{ESC(titulo)}">']
    passo = maximo / 4
    for k in range(5):
        v = passo * k
        x = esq + util * v / maximo
        s.append(f'<line x1="{x:.1f}" y1="{topo}" x2="{x:.1f}" y2="{alt-30}" stroke="{GRID}"/>')
        s.append(f'<text x="{x:.1f}" y="{alt-12}" fill="{MUTED}" font-size="12" text-anchor="middle">{br(v)}{sufixo}</text>')
    for i, (rot, val) in enumerate(itens):
        y = topo + i * alt_l + 10
        w = max(util * val / maximo, 6)
        s.append(f'<text x="{esq-12}" y="{y+16}" fill="{INK}" font-size="14" text-anchor="end">{ESC(rot)}</text>')
        s.append(f'<rect x="{esq}" y="{y}" width="{w:.1f}" height="24" fill="{BLUE}" stroke="{INK}" stroke-width="2"/>')
        s.append(f'<text x="{esq+w+8:.1f}" y="{y+17}" fill="{INK}" font-size="14" font-weight="700">{br(val, 1 if val % 1 else 0)}{sufixo}</text>')
    s.append("</svg>")
    return f'<figure><figcaption class="tit">{ESC(titulo)}</figcaption>{"".join(s)}<figcaption class="fonte">Fonte: {ESC(fonte)}</figcaption></figure>'


def medidor(titulo, pct, rot_a, rot_b, fonte):
    return (f'<figure class="medidor"><figcaption class="tit">{ESC(titulo)}</figcaption>'
            f'<div class="trilho"><span style="width:{pct}%"><b>{br(pct,1)}%</b></span></div>'
            f'<div class="med-leg"><span>■ {ESC(rot_a)}</span><span>□ {ESC(rot_b)}</span></div>'
            f'<figcaption class="fonte">Fonte: {ESC(fonte)}</figcaption></figure>')


# ---------------- blocos ----------------
def evid(lista):
    return '<ul class="evid">' + "".join(
        f'<li><span class="tag tag-{e["tipo"]}">{SIMB[e["tipo"]]} {ROT[e["tipo"]]}</span><span>{ESC(e["texto"])} <cite>{ESC(e["fonte"])}</cite></span></li>'
        for e in lista) + "</ul>"


def tabela_criterios(p):
    linhas = "".join(
        f'<tr><td class="mono">{c["id"]}</td><td>{ESC(c["criterio"])}<span class="como">{ESC(c["como_medir"])}</span></td>'
        f'<td><b>{ESC(c["limite"])}</b></td><td><span class="auto auto-{c["automacao"]}">{AUTO[c["automacao"]]}</span></td></tr>'
        for c in p["criterios"])
    return ('<table class="crit"><thead><tr><th>Código</th><th>Critério e como medir</th><th>Limite</th><th>Quem faz</th></tr></thead>'
            f"<tbody>{linhas}</tbody></table>")


def padrao(p):
    niveis = ""
    if "niveis" in p:
        niveis = '<dl class="niveis">' + "".join(f"<dt>Nível {k}</dt><dd>{ESC(v)}</dd>" for k, v in p["niveis"].items()) + "</dl>"
    return f'''
<section class="padrao">
  <header><span class="cod">{p["id"]}</span><h3>{ESC(p["nome"])}</h3></header>
  <p class="regra">{ESC(p["regra"])}</p>
  <div class="simples"><b>Em palavras simples.</b> {ESC(p["em_palavras_simples"])}</div>
  <div class="duas">
    <div><h4>Exemplos</h4><ul>{"".join(f"<li>{ESC(x)}</li>" for x in p["exemplos"])}</ul>
         <h4>O que a PRISMA faz</h4><ul>{"".join(f"<li>{ESC(x)}</li>" for x in p["como_a_plataforma_aplica"])}</ul>{niveis}</div>
    <div class="lado"><h4>Como conferir</h4><p>{ESC(p["verificacao"])}</p><h4>Também ajuda</h4><p>{ESC(p["ajuda_tambem"])}</p></div>
  </div>
  <h4>Critérios que o código verifica</h4>{tabela_criterios(p)}
  <h4>Em que se baseia</h4>{evid(p["evidencias"])}
</section>'''


def necessidades():
    out = []
    for n in D["necessidades"]:
        reg = f'<span class="reg">{br(n["registros_2024"])} registros em 2024</span>' if n.get("registros_2024") else ""
        extra = ""
        if n.get("limite_da_plataforma"):
            extra += f'<p class="lim"><b>Limite da PRISMA.</b> {ESC(n["limite_da_plataforma"])}</p>'
        if n.get("nota"):
            extra += f'<p class="nota">{ESC(n["nota"])}</p>'
        out.append(f'''<article class="nec"><header><h3>{ESC(n["nome"])}</h3>{reg}</header>
<p>{ESC(n["em_palavras_simples"])}</p>
<p class="barr"><b>Barreiras comuns no material:</b> {ESC("; ".join(n["barreiras"]))}.</p>
<p class="pads"><b>Padrões principais:</b> {" ".join(f'<span class="mono">{x}</span>' for x in n["padroes"])}</p>{extra}</article>''')
    return '<div class="necs">' + "".join(out) + "</div>"


def mapa():
    ids = [p["id"] for p in D["padroes"]]
    cab = "".join(f"<th>{i}</th>" for i in ids)
    linhas = ""
    for n in D["necessidades"]:
        cel = ""
        for i in ids:
            if i in n["padroes"]:
                ordem = n["padroes"].index(i)
                cel += f'<td class="{"forte" if ordem < 2 else "medio"}">{"●" if ordem < 2 else "○"}</td>'
            else:
                cel += "<td></td>"
        linhas += f'<tr><th>{ESC(n["nome"])}</th>{cel}</tr>'
    return (f'<table class="mapa"><thead><tr><th></th>{cab}</tr></thead><tbody>{linhas}</tbody></table>'
            '<p class="fonte-solta">● padrão central para essa necessidade · ○ padrão de apoio. Todos os padrões valem para todos os alunos.</p>')


def fluxo():
    return '<ol class="fluxo">' + "".join(
        f'<li><span class="n">{i}</span><b>{ESC(f["etapa"])}</b><span>{ESC(f["texto"])} <em class="mono">{" ".join(f["padroes"])}</em></span></li>'
        for i, f in enumerate(D["fluxo"], 1)) + "</ol>"


def versoes():
    v = "".join(f'<tr><td><b>{ESC(x["nome"])}</b><span class="como">o aluno vê: "{ESC(x["rotulo_aluno"])}"</span></td><td class="mono">{" ".join(x["aplica"])}</td><td>{ESC(x["para"])}</td></tr>' for x in D["versoes_geradas"])
    s = "".join(f'<tr><td><b>{ESC(x["nome"])}</b></td><td class="mono">{" ".join(x["padroes"])}</td><td>{ESC(x["texto"])}</td></tr>' for x in D["saidas_para_o_professor"])
    return (f'<h3 class="h3s">Versões para os alunos</h3><table class="tab"><thead><tr><th>Versão</th><th>Padrões</th><th>Para quem</th></tr></thead><tbody>{v}</tbody></table>'
            f'<h3 class="h3s">Saídas para o professor</h3><table class="tab"><thead><tr><th>Saída</th><th>Padrões</th><th>O que é</th></tr></thead><tbody>{s}</tbody></table>')


def automacao():
    c = Counter(cr["automacao"] for p in D["padroes"] for cr in p["criterios"])
    tot = sum(c.values())
    itens = [(AUTO[k], c[k]) for k in ("automatico", "ia_revisao", "manual")]
    return barras_h(f"Os {tot} critérios por quem faz a verificação", itens, "padroes.json", maximo=max(30, max(v for _, v in itens)), sufixo="", esq=150)


ICO = {
    "sol": '<svg viewBox="0 0 40 40" class="ico"><circle cx="20" cy="20" r="8" fill="#A3401F"/><g stroke="#A3401F" stroke-width="3" stroke-linecap="round"><path d="M20 3v6M20 31v6M3 20h6M31 20h6M8 8l4 4M28 28l4 4M8 32l4-4M28 12l4-4"/></g></svg>',
    "nuvem": '<svg viewBox="0 0 40 40" class="ico"><path d="M12 30h17a7 7 0 0 0 0-14 10 10 0 0 0-19 3 6 6 0 0 0 2 11z" fill="#4A4F6A"/></svg>',
    "chuva": '<svg viewBox="0 0 40 40" class="ico"><path d="M12 22h17a7 7 0 0 0 0-14 10 10 0 0 0-19 3 6 6 0 0 0 2 11z" fill="#4A4F6A"/><g stroke="#1F6FB2" stroke-width="3" stroke-linecap="round"><path d="M14 27l-2 6M21 27l-2 6M28 27l-2 6"/></g></svg>',
    "ciclo": '<svg viewBox="0 0 40 40" class="ico"><g fill="none" stroke="#1F6FB2" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"><path d="M31 15a12 12 0 0 0-22 0"/><path d="M9 25a12 12 0 0 0 22 0"/><path d="M31 8v8h-8M9 32v-8h8"/></g></svg>',
}


def exemplo():
    orig = ("O ciclo hidrológico consiste na circulação contínua da água entre a superfície terrestre e a atmosfera, impulsionada pela energia solar. "
            "Ao ser aquecida, a água de oceanos, rios e lagos sofre evaporação; o vapor, ao ascender e resfriar-se, condensa-se formando nuvens, que, saturadas, originam a precipitação.")
    n3 = ("O ciclo da água é a circulação contínua da água entre a superfície da Terra e a atmosfera. A energia do Sol movimenta esse ciclo. "
          "O calor faz a água de oceanos, rios e lagos <b>evaporar</b>. O vapor sobe, esfria e se <b>condensa</b>: assim se formam as nuvens. "
          "Quando as nuvens ficam carregadas, a água cai. Isso se chama <b>precipitação</b>.")
    n2 = ["A água da Terra está sempre em movimento.", "O Sol esquenta a água dos rios e do mar.", "A água vira vapor e sobe para o céu.",
          "Lá em cima, o vapor esfria e forma as nuvens.", "As nuvens ficam pesadas de água.", "Então a água cai. É a chuva.", "Depois, tudo começa de novo."]
    n1 = [("sol", "O Sol esquenta a água."), ("nuvem", "A água sobe e vira nuvem."), ("chuva", "A nuvem solta a chuva."), ("ciclo", "E tudo começa de novo.")]
    return f'''<div class="lf-grade">
<div class="lf-caixa"><p class="lf-rot">Original · exemplo criado pelo time</p><p>{orig}</p></div>
<div class="lf-caixa"><p class="lf-rot">Nível III · com glossário</p><p>{n3}</p><p class="glos"><b>evaporar</b>: virar vapor · <b>condensar</b>: o vapor voltar a ser gotinhas · <b>precipitação</b>: chuva, neve ou granizo</p></div>
<div class="lf-caixa"><p class="lf-rot">Nível II · uma frase por linha</p><p class="linhas">{"".join(f"<span>{x}</span>" for x in n2)}</p></div>
<div class="lf-caixa"><p class="lf-rot">Nível I · pouco texto, imagem de apoio</p>{"".join(f'<div class="lf1">{ICO[k]}<span>{t}</span></div>' for k, t in n1)}</div>
</div>
<div class="duas" style="margin-top:12pt">
<div><h4>Atividade mão na massa (P7)</h4><ol><li><b>Mexer:</b> aquecer água num pote transparente tampado com um prato frio e observar as gotas.</li><li><b>Desenhar:</b> desenhar o pote e as setas do caminho da água.</li><li><b>Escrever:</b> ligar cada parte do desenho às palavras evaporar, condensar e chover.</li></ol></div>
<div class="lado"><h4>Conexões (P8)</h4><p><b>Matemática:</b> medir a chuva da semana com um pluviômetro de garrafa PET. <b>Geografia:</b> os rios da região. <b>Música:</b> canções sobre chuva. <b>Tema transversal:</b> Educação Ambiental.</p></div>
</div>'''


def documento(css_fontes):
    dd = D["dados"]
    reg = dd["registros_por_tipo_2024"]
    cc = dd["classes_comuns_4a17_2025"]
    sa = dd["escolas_sem_acessibilidade_2024"]
    esc = dd["escolarizacao_por_idade_2022"]
    resumo = "".join(f'<li><span class="cod">{p["id"]}</span><b>{ESC(p["nome"])}</b><span>{ESC(p["regra"])}</span></li>' for p in D["padroes"])
    princ = "".join(f'<li><b>{ESC(x["nome"])}.</b> {ESC(x["texto"])}</li>' for x in D["principios"])
    glos = "".join(f'<dt>{ESC(g["termo"])}</dt><dd>{ESC(g["definicao"])}</dd>' for g in D["glossario"])
    refs = "".join(f"<li>{ESC(r)}</li>" for r in D["referencias"])
    ncrit = sum(len(p["criterios"]) for p in D["padroes"])
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Manual PRISMA</title>
<style>{css_fontes}{CSS}</style></head><body>

<section class="capa">
  <img class="prisma" src="{LOGO}" alt="Logo da PRISMA: um prisma de vidro que recebe um feixe de luz e solta um arco-íris">
  <p class="eyebrow">PRISMA · Manual de padrões · versão {ESC(D["versao"])}</p>
  <h1>Manual PRISMA</h1>
  <p class="sigla">{ESC(D["sigla"])}</p>
  <p class="sub">{ESC(D["lema"])} Este manual explica as regras que a plataforma usa para transformar cada material. Mostra em que pesquisas cada regra se apoia e lista os {ncrit} critérios que o código verifica.</p>
  <ul class="capa-leitores">
    <li><b>Professores e escolas</b><span>Partes 1 a 5: por que, princípios, como funciona, quem são os estudantes e os 10 padrões.</span></li>
    <li><b>Time de desenvolvimento</b><span>Parte 6: como o código usa este manual. As tabelas de critérios estão na Parte 5.</span></li>
    <li><b>Famílias</b><span>Parte 9, em linguagem simples.</span></li>
    <li><b>Estudantes</b><span>Parte 10, em Leitura Fácil.</span></li>
  </ul>
  <p class="nota-capa">Este manual segue as próprias regras. O texto usa a Atkinson Hyperlegible Next, criada para leitores com baixa visão. Os títulos usam a Pixelify Sans, a fonte pixel do site, só em frases curtas. Os números ficam sempre na fonte do texto. O texto é alinhado à esquerda, e nenhuma informação passa só por cor. Time Carcará 3301, Hackathon LEPV 2026.</p>
</section>

<section class="parte">
  <p class="eyebrow">Parte 1</p><h2>Por que a PRISMA existe</h2>
  <p>Quase todos os estudantes com deficiência já estudam na mesma sala que os colegas. O desafio agora é que eles <b>aprendam</b> junto com a turma. Para isso, o material da aula precisa chegar a todos. E o professor, que já não tem tempo, precisa de ajuda para adaptá-lo.</p>
  <div class="numeros">
    <div><b>2,5 milhões</b><span>matrículas na educação especial em 2025, 82% a mais que em 2021 (INEP)</span></div>
    <div><b>{cc["comuns"]}%</b><span>dos estudantes de 4 a 17 anos da educação especial estão em classes comuns (INEP, 2025)</span></div>
    <div><b>{br(dd["formacao"]["regentes_com_formacao_continuada_2024"],1)}%</b><span>dos professores regentes têm formação continuada em educação especial (2024)</span></div>
  </div>
  {rosca(reg["fatias"], "Registros da educação especial por tipo, 2024", reg["fonte"], reg["nota"])}
  <p>Deficiência intelectual e autismo somam quatro em cada cinco registros. Por isso Linguagem Simples (P3), estrutura previsível (P6) e o concreto (P7) estão no centro da PRISMA. Mas a plataforma serve a toda a turma: os mesmos padrões ajudam quem não tem deficiência nenhuma.</p>
  {barras_h("Pessoas com deficiência que frequentam a escola, por idade (2022)", [(f["faixa"], f["valor"]) for f in esc["faixas"]], esc["fonte"])}
  <p>A escola chega a quase todas as crianças com deficiência, mas elas vão ficando pelo caminho. Entre 18 e 24 anos, só uma em cada quatro ainda estuda.</p>
  {medidor("Escolas sem nenhum recurso de acessibilidade, 2024", sa["sem"], f"{br(sa['escolas_sem'])} escolas sem nenhum recurso", "escolas com pelo menos um recurso", sa["fonte"])}
  <h3 class="h3s">O que os professores dizem</h3>
  <ul class="falas">
    <li>Falta tempo para planejar adaptações. É a principal queixa. <cite>Marques &amp; Duarte (2013)</cite></li>
    <li>Sentem angústia por uma formação que consideram insuficiente. <cite>Tavares, Santos &amp; Freitas (2016), 52 professores</cite></li>
    <li>Conhecem o PEI na teoria, mas não se sentem preparados para aplicá-lo. <cite>Santos (2024), 32 docentes</cite></li>
    <li>Sentem-se sozinhos e sem materiais adequados. <cite>Brito &amp; Flores (2023)</cite></li>
    <li>As apostilas são usadas sem conexão entre disciplinas, porque planejar em conjunto exige um tempo que não existe. <cite>Professora do time PRISMA</cite></li>
  </ul>
</section>

<section class="parte">
  <p class="eyebrow">Parte 2</p><h2>Princípios</h2>
  <ol class="principios">{princ}</ol>
</section>

<section class="parte">
  <p class="eyebrow">Parte 3</p><h2>Como a PRISMA funciona</h2>
  <p>Uma aula entra e várias versões saem. O ciclo abaixo se repete a cada material, e o material melhora a cada volta.</p>
  {fluxo()}
  {versoes()}
</section>

<section class="parte">
  <p class="eyebrow">Parte 4</p><h2>Quem são os estudantes</h2>
  <p>A PRISMA não pergunta diagnósticos. Esta parte existe para quem usa a plataforma entender as necessidades mais comuns em sala. Mostra também as barreiras que cada uma encontra no material e os padrões que mais ajudam. As descrições são simples de propósito; cada pessoa é única.</p>
  {necessidades()}
  <div class="bloco-mapa"><h3 class="h3s">Mapa: necessidades × padrões</h3>
  {mapa()}</div>
</section>

<section class="parte">
  <p class="eyebrow">Parte 5</p><h2>Os 10 padrões de transformação</h2>
  <p>Cada padrão tem uma regra, uma explicação simples, o que a plataforma faz e como conferir. Traz também os critérios que o código verifica e as evidências em que se apoia.</p>
  <ul class="chave">
    <li><span class="tag tag-dados">● Dados</span> estudo com dados coletados</li>
    <li><span class="tag tag-pratica">◆ Prática</span> relato, revisão ou estudo qualitativo</li>
    <li><span class="tag tag-norma">■ Norma</span> norma técnica ou lei</li>
    <li><span class="tag tag-projeto">○ Projeto</span> decisão do time, a validar</li>
  </ul>
  <ul class="resumo">{resumo}</ul>
  {"".join(padrao(p) for p in D["padroes"])}
</section>

<section class="parte">
  <p class="eyebrow">Parte 6 · Para o time de desenvolvimento</p><h2>Como o código usa este manual</h2>
  <p>Tudo o que está nas tabelas de critérios vive num único arquivo: <span class="mono">docs/manual/padroes.json</span>. O mesmo arquivo gera este PDF e a aba de instruções do site. Se uma regra mudar, mude no arquivo e rode o gerador. Assim o PDF, o site e o código passam a concordar.</p>
  <h3 class="h3s">Ordem de verificação sugerida</h3>
  <ol class="passos">
    <li><b>Ler o material</b> e separar texto, imagens, tabelas e cores.</li>
    <li><b>Rodar os critérios automáticos</b> (P1.1, P1.3, P2.x, P3.1, P3.2, P3.5, P4.1, P4.3). São regras com limite numérico ou busca de padrões, sem IA.</li>
    <li><b>Chamar a IA</b> para os critérios marcados como "IA + revisão". O pedido leva a regra e o limite de cada um.</li>
    <li><b>Conferir o resultado da IA</b> com os critérios automáticos de novo. Frase com mais de 20 palavras volta para reescrita (P3.1). Conceito-chave que sumiu bloqueia (P3.7).</li>
    <li><b>Montar o relatório de barreiras</b> com o código de cada critério. Depois, enviar para a fila de revisão do professor (P10.1).</li>
  </ol>
  {automacao()}
  <h3 class="h3s">Como um critério aparece no arquivo</h3>
  <pre class="codigo">{{
  "id": "P3.1",
  "criterio": "Palavras por frase.",
  "como_medir": "Contar palavras entre pontos finais.",
  "limite": "≤ 20 em todos os níveis; ≤ 15 no nível II e ≤ 10 no nível I (projeto)",
  "automacao": "automatico"
}}</pre>
  <p>O campo <span class="mono">automacao</span> diz quem verifica. Pode ser <b>automatico</b> (o código, sozinho), <b>ia_revisao</b> (a IA propõe e o professor confere) ou <b>manual</b> (uma pessoa).</p>
</section>

<section class="parte">
  <p class="eyebrow">Parte 7</p><h2>Exemplo completo: o ciclo da água</h2>
  <p>O mesmo conteúdo em quatro níveis de leitura. Vêm junto a atividade concreta e as conexões que a PRISMA sugere ao professor.</p>
  {exemplo()}
</section>

<section class="parte">
  <p class="eyebrow">Parte 8</p><h2>Limites e transparência</h2>
  <ul class="limites">
    <li><b>A PRISMA não faz diagnóstico.</b> Se a família ou a escola notar dificuldades persistentes, o caminho é procurar a equipe da escola. Também vale procurar um profissional de saúde.</li>
    <li><b>A IA pode errar.</b> Uma simplificação pode mudar o sentido de um conceito, e modelos de linguagem podem inventar informação. Por isso nenhuma versão é publicada sem revisão (P10) e os conceitos-chave são conferidos (P3.7).</li>
    <li><b>Simplificar não garante compreensão.</b> As pesquisas com leitores reais têm resultados variados. Por isso existe a avaliação dos alunos, com estrelas e sugestão (P9).</li>
    <li><b>Não substitui pessoas.</b> AEE, intérprete de Libras, guia-intérprete, professor de apoio e transcrição profissional em braile continuam necessários. A PRISMA não gera Libras.</li>
    <li><b>Recolorir imagens não serve para todos</b> os tipos de daltonismo. A regra principal é acrescentar símbolos e rótulos.</li>
    <li><b>Muitas evidências vêm de estudos pequenos</b> e qualitativos. Os parâmetros marcados como ○ Projeto precisam ser testados.</li>
    <li><b>A divisão por tipo de deficiência conta registros</b>, não pessoas: um estudante pode ter mais de um registro.</li>
  </ul>
</section>

<section class="parte familia">
  <p class="eyebrow">Parte 9 · Para famílias</p><h2>O que a PRISMA faz pelo seu filho ou filha</h2>
  <p>O professor coloca o material da aula na PRISMA. A PRISMA prepara versões diferentes do mesmo conteúdo. Por exemplo: letras maiores, um texto mais direto ou um áudio.</p>
  <p>Seu filho ou filha escolhe a versão que funciona melhor. Todos os colegas podem usar as mesmas versões. Ninguém é separado.</p>
  <p>O professor também recebe ideias de atividades com objetos, como blocos e quebra-cabeças. E vê como o assunto aparece em outras matérias.</p>
  <h3 class="h3s">Como apoiar em casa</h3>
  <ul>
    <li>Peça para a criança mostrar qual versão ela prefere e por quê.</li>
    <li>Leiam juntos a versão de texto mais direto antes de uma prova.</li>
    <li>Use o áudio fora da tela, por exemplo no caminho para a escola.</li>
    <li>Repita em casa a atividade com objetos que veio no guia.</li>
    <li>Conte ao professor o que funciona em casa.</li>
  </ul>
  <h3 class="h3s">Perguntas que você pode fazer à escola</h3>
  <ul>
    <li>Meu filho ou filha tem um Plano Educacional Individualizado (PEI)? Posso participar? Desde 2025, esse plano é obrigatório para os estudantes da educação especial.</li>
    <li>Há Atendimento Educacional Especializado (AEE) na escola?</li>
    <li>Como vocês vão avaliar o que ele ou ela aprendeu?</li>
  </ul>
  <p class="aviso">A PRISMA nunca diz se uma criança tem uma deficiência. Se você tem dúvidas sobre o desenvolvimento do seu filho ou filha, converse com a escola. Procure também um profissional de saúde. Para receber apoio na escola, como o profissional de apoio, a lei não exige laudo.</p>
</section>

<section class="parte estudante">
  <p class="eyebrow">Parte 10 · Para estudantes</p><h2>A Sala de Materiais é sua</h2>
  <p class="linhas"><span>Aqui ficam os materiais da sua turma.</span><span>Cada material tem jeitos diferentes de estudar.</span><span>Você pode ler com letras grandes.</span><span>Você pode ler um texto mais curto.</span><span>Você pode ouvir.</span><span>Você escolhe o jeito que é melhor para você.</span><span>Pode trocar de jeito quando quiser.</span><span>No fim, tem três perguntas rápidas.</span><span>Se algo estiver difícil, fale com o seu professor.</span></p>
</section>

<section class="parte">
  <p class="eyebrow">Glossário</p><h2>Palavras deste manual</h2>
  <dl class="glossario">{glos}</dl>
</section>

<section class="parte refs">
  <p class="eyebrow">Referências</p><h2>Fontes usadas neste manual</h2>
  <ol>{refs}</ol>
</section>
</body></html>'''


CSS = """
@page { size: A4; }
:root { --ink:#1E2235; --muted:#4A4F6A; --line:#D9D3C4; --soft:#F3EDDF; --blue:#1F6FB2; --sol:#FFC93C;
  --display:'Pixelify Sans','Atkinson Hyperlegible Next',system-ui,sans-serif; --body:'Atkinson Hyperlegible Next',system-ui,sans-serif; --mono:'Departure Mono',ui-monospace,monospace; }
* { box-sizing:border-box }
body { margin:0; color:var(--ink); background:#fff; font:11pt/1.55 var(--body); }
h1,h2,h3,h4 { font-family:var(--display); line-height:1.2; margin:0; text-wrap:balance; }
h2 { font-size:22pt; font-weight:400; margin-bottom:10pt; }
h3 { font-size:14pt; font-weight:400; }
.h3s { margin:16pt 0 6pt; }
h4 { font-size:9.5pt; font-weight:400; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); margin:10pt 0 4pt; }
p { margin:0 0 8pt; max-width:64ch; }
ul,ol { margin:0 0 8pt; padding-left:16pt; }
li { margin-bottom:3pt; }
cite { font-style:normal; color:var(--muted); font-size:9.5pt; }
.eyebrow { font-family:var(--mono); font-size:9pt; letter-spacing:.08em; text-transform:uppercase; color:var(--blue); margin-bottom:4pt; }
.mono { font-family:var(--mono); font-size:.92em; }
.capa { min-height:250mm; display:flex; flex-direction:column; justify-content:center; break-after:page; }
.prisma { width:66mm; height:auto; margin-bottom:12pt; image-rendering:pixelated; }
.capa h1 { font-size:44pt; font-weight:400; letter-spacing:-.01em; margin:4pt 0 2pt; }
.sigla { font-family:var(--display); font-size:13pt; color:var(--muted); margin-bottom:14pt; }
.capa .sub { font-size:13pt; max-width:48ch; }
.capa-leitores { list-style:none; padding:0; margin:18pt 0; display:grid; gap:0; }
.capa-leitores li { display:grid; grid-template-columns:48mm 1fr; gap:8pt; padding:8pt 0; border-top:1px solid var(--line); }
.capa-leitores b { font-family:var(--display); font-weight:400; }
.nota-capa { font-size:9pt; color:var(--muted); max-width:72ch; }
.parte { break-before:page; }
.numeros { display:grid; grid-template-columns:repeat(3,1fr); gap:10pt; margin:12pt 0; }
.numeros div { border-top:3pt solid var(--ink); padding-top:6pt; }
.numeros b { display:block; font-family:var(--body); font-size:21pt; font-weight:700; }
.numeros span { font-size:9.5pt; color:var(--muted); }
.fonte-solta { font-size:9pt; color:var(--muted); }
figure { margin:14pt 0; break-inside:avoid; }
.grafico { width:100%; height:auto; font-family:var(--body); }
figcaption.tit { font-family:var(--display); font-weight:400; font-size:11.5pt; margin-bottom:6pt; }
figcaption.fonte { font-size:8.5pt; color:var(--muted); margin-top:4pt; }
.rosca-grade { display:grid; grid-template-columns:62mm 1fr; gap:14pt; align-items:center; }
.rosca { width:62mm; height:auto; font-family:var(--body); }
.leg-rosca { list-style:none; padding:0; margin:0; font-size:10pt; }
.leg-rosca li { display:grid; grid-template-columns:12pt 1fr auto 24mm; gap:6pt; align-items:baseline; padding:4pt 0; border-top:1px solid var(--line); }
.leg-rosca i { width:10pt; height:10pt; display:inline-block; transform:translateY(1pt); outline:1.5pt solid var(--ink); }
.leg-rosca b { font-variant-numeric:tabular-nums; }
.leg-rosca em { font-style:normal; color:var(--muted); text-align:right; font-variant-numeric:tabular-nums; }
.medidor .trilho { height:22pt; background:var(--soft); border:1px solid var(--line); overflow:hidden; }
.medidor .trilho span { display:flex; align-items:center; justify-content:flex-end; height:100%; background:var(--ink); color:#fff; padding-right:6pt; font-size:10pt; }
.med-leg { display:flex; gap:16pt; font-size:9.5pt; margin-top:4pt; }
.falas { list-style:none; padding:0; }
.falas li { padding:4pt 0 4pt 12pt; border-left:2pt solid var(--line); margin-bottom:6pt; }
.falas cite { display:block; }
.principios li { margin-bottom:7pt; }
.fluxo { list-style:none; padding:0; }
.fluxo li { display:grid; grid-template-columns:18pt 26mm 1fr; gap:8pt; align-items:baseline; padding:7pt 0; border-top:1px solid var(--line); }
.fluxo .n { font-family:var(--mono); color:var(--blue); }
.fluxo b { font-family:var(--display); font-weight:400; }
.fluxo em { font-style:normal; color:var(--blue); }
.tab { width:100%; border-collapse:collapse; font-size:9.5pt; }
.tab th { text-align:left; font-family:var(--display); font-weight:400; border-bottom:1.5pt solid var(--ink); padding:4pt 6pt 4pt 0; }
.tab td { border-bottom:1px solid var(--line); padding:5pt 6pt 5pt 0; vertical-align:top; }
.como { display:block; color:var(--muted); font-size:8.8pt; margin-top:1pt; }
.necs { display:grid; grid-template-columns:1fr 1fr; gap:10pt; }
.nec { border:1px solid var(--line); padding:8pt 10pt; font-size:9.5pt; break-inside:avoid; }
.nec header { display:flex; justify-content:space-between; gap:8pt; align-items:baseline; margin-bottom:4pt; }
.nec h3 { font-size:11.5pt; }
.nec .reg { font-family:var(--mono); font-size:8pt; color:var(--muted); white-space:nowrap; }
.nec p { margin-bottom:4pt; }
.nec .lim { background:var(--soft); padding:4pt 6pt; }
.nec .nota { color:var(--muted); font-size:8.8pt; }
.mapa { border-collapse:collapse; font-size:9pt; width:100%; break-inside:avoid; }
.mapa th, .mapa td { border:1px solid var(--line); padding:3pt 4pt; text-align:center; }
.mapa tbody th { text-align:left; font-weight:400; }
.mapa thead th { font-family:var(--mono); font-weight:400; }
.mapa td.forte { background:var(--ink); color:#fff; }
.mapa td.medio { background:var(--soft); }
.chave { list-style:none; padding:0; display:grid; grid-template-columns:1fr 1fr; gap:4pt 14pt; font-size:10pt; }
.tag { display:inline-block; font-family:var(--mono); font-size:8.5pt; letter-spacing:.04em; text-transform:uppercase; padding:1pt 5pt; border:1px solid var(--ink); white-space:nowrap; }
.tag-dados { background:var(--ink); color:#fff; }
.tag-norma { background:var(--soft); }
.tag-projeto { border-style:dashed; color:var(--muted); border-color:var(--muted); }
.resumo { list-style:none; padding:0; margin:12pt 0; }
.resumo li { display:grid; grid-template-columns:24pt 44mm 1fr; gap:8pt; padding:5pt 0; border-top:1px solid var(--line); font-size:9.5pt; }
.cod { font-family:var(--mono); font-weight:400; color:var(--blue); }
.padrao { break-before:page; }
.padrao header { display:flex; align-items:baseline; gap:10pt; border-bottom:2pt solid var(--ink); padding-bottom:6pt; margin-bottom:8pt; }
.padrao header .cod { font-size:24pt; }
.padrao h3 { font-size:19pt; }
.regra { font-family:var(--display); font-size:12.5pt; font-weight:400; max-width:56ch; }
.simples { background:var(--soft); padding:7pt 10pt; font-size:10.5pt; margin-bottom:6pt; }
.duas { display:grid; grid-template-columns:1.3fr 1fr; gap:14pt; }
.duas ul, .duas ol { font-size:10pt; }
.lado { border-left:2pt solid var(--line); padding-left:10pt; font-size:10pt; }
.niveis { display:grid; grid-template-columns:auto 1fr; gap:3pt 8pt; font-size:9.5pt; margin:6pt 0; }
.niveis dt { font-family:var(--mono); font-weight:400; }
.niveis dd { margin:0; }
.crit { width:100%; border-collapse:collapse; font-size:9pt; }
.crit th { text-align:left; font-family:var(--display); font-weight:400; border-bottom:1.5pt solid var(--ink); padding:3pt 6pt 3pt 0; }
.crit td { border-bottom:1px solid var(--line); padding:4pt 6pt 4pt 0; vertical-align:top; }
.crit tr { break-inside:avoid; }
.crit td:first-child { width:12mm; } .crit td:nth-child(3) { width:36mm; } .crit td:last-child { width:22mm; }
.auto { font-family:var(--mono); font-size:8.5pt; text-transform:uppercase; letter-spacing:.03em; padding:1pt 4pt; border:1px solid var(--ink); white-space:nowrap; }
.auto-automatico { background:var(--ink); color:#fff; }
.auto-ia_revisao { background:var(--soft); }
.auto-manual { border-style:dashed; }
.evid { list-style:none; padding:0; font-size:9.5pt; }
.evid li { display:grid; grid-template-columns:20mm 1fr; gap:8pt; padding:4pt 0; border-top:1px solid var(--line); break-inside:avoid; }
.evid cite { display:block; }
.passos li { margin-bottom:5pt; }
.codigo { font-family:var(--mono); font-size:8.5pt; background:var(--soft); padding:8pt 10pt; white-space:pre-wrap; }
.lf-grade { display:grid; grid-template-columns:1fr 1fr; gap:10pt; }
.lf-caixa { border:1px solid var(--line); padding:8pt 10pt; font-size:10pt; break-inside:avoid; }
.lf-rot { font-family:var(--mono); font-size:8pt; text-transform:uppercase; letter-spacing:.05em; color:var(--blue); margin-bottom:4pt; }
.linhas span { display:block; }
.glos { font-size:8.8pt; color:var(--muted); border-top:1px dashed var(--line); padding-top:4pt; }
.lf1 { display:flex; align-items:center; gap:8pt; margin-bottom:5pt; font-size:11.5pt; }
.ico { width:24pt; height:24pt; flex:none; }
.bloco-mapa { break-before:page; }
.limites li { margin-bottom:7pt; }
.familia p, .familia li { font-size:12pt; }
.aviso { border:1.5pt solid var(--ink); padding:8pt 10pt; margin-top:12pt; }
.estudante .linhas { font-size:16pt; line-height:1.75; }
.glossario { display:grid; grid-template-columns:36mm 1fr; gap:5pt 10pt; font-size:10pt; }
.glossario dt { font-family:var(--display); font-weight:400; }
.glossario dd { margin:0; }
.refs ol { font-size:8.8pt; padding-left:14pt; }
.refs li { margin-bottom:4pt; }
"""


def css_fontes(embutir=True):
    """As fontes são as do site (web/assets/fontes), as mesmas da interface."""
    def face(fam, arq, peso="400"):
        if embutir:
            b64 = base64.b64encode((FONTES / arq).read_bytes()).decode()
            return f"@font-face{{font-family:'{fam}';src:url(data:font/woff2;base64,{b64}) format('woff2');font-weight:{peso};}}"
        return f"@font-face{{font-family:'{fam}';src:url('../../web/assets/fontes/{arq}') format('woff2');font-weight:{peso};}}"
    return "".join([face("Atkinson Hyperlegible Next", "atkinson-400.woff2"), face("Atkinson Hyperlegible Next", "atkinson-700.woff2", "700"),
                    face("Pixelify Sans", "pixelify-400.woff2"), face("Pixelify Sans", "pixelify-700.woff2", "700"),
                    face("Departure Mono", "departure-mono.woff2")])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sem-pdf", action="store_true")
    a = ap.parse_args()
    if a.sem_pdf:
        return
    from playwright.sync_api import sync_playwright
    tmp = AQUI / "_manual_pdf.html"
    tmp.write_text(documento(css_fontes(True)), encoding="utf-8")
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        pg = nav.new_page()
        pg.goto(tmp.resolve().as_uri())
        pg.wait_for_timeout(500)
        pg.pdf(path=str(AQUI / "manual-prisma-v1.pdf"), format="A4", print_background=True, display_header_footer=True,
               header_template="<span></span>",
               footer_template='<div style="width:100%;font:8px sans-serif;color:#4A4F6A;padding:0 18mm;display:flex;justify-content:space-between">'
                               '<span>Manual PRISMA · v1.0 · Time Carcará 3301</span><span><span class="pageNumber"></span> de <span class="totalPages"></span></span></div>',
               margin={"top": "18mm", "bottom": "20mm", "left": "18mm", "right": "18mm"})
        nav.close()
    tmp.unlink()


if __name__ == "__main__":
    main()
