#!/usr/bin/env python3
"""Gera o Manual de Acessibilidade (HTML + PDF) a partir de padroes.json.

Uso:  python3 docs/manual/build_manual.py [--fontes PASTA_COM_TTF]
Saída: docs/manual/manual.html e docs/manual/manual-carcara-v0.1.pdf

O conteúdo dos padrões vem SÓ de padroes.json (fonte única, a mesma que o site usa).
O texto corrido das outras seções está aqui, em TEXTO_*.
"""
import argparse
import base64
import html
import json
from pathlib import Path

AQUI = Path(__file__).parent
P = json.loads((AQUI / "padroes.json").read_text(encoding="utf-8"))

ESC = html.escape
SIMBOLO = {"dados": "●", "pratica": "◆", "norma": "■", "projeto": "○"}
ROTULO = {"dados": "Dados", "pratica": "Prática", "norma": "Norma", "projeto": "Projeto"}

# ---------- gráficos (SVG estático para impressão) ----------
INK, MUTED, GRID, BLUE, AMBER = "#142033", "#4A5668", "#D8DEE6", "#1F5FBF", "#C26A00"


def barras_h(titulo, dados, fonte, maximo=100, largura=640):
    """Barras horizontais, série única (sem legenda: o título nomeia a série)."""
    alt_linha, topo, esq = 44, 8, 150
    altura = topo + alt_linha * len(dados) + 34
    util = largura - esq - 70
    s = [f'<svg viewBox="0 0 {largura} {altura}" role="img" aria-label="{ESC(titulo)}" class="grafico">']
    for v in range(0, maximo + 1, 25):
        x = esq + util * v / maximo
        s.append(f'<line x1="{x:.1f}" y1="{topo}" x2="{x:.1f}" y2="{altura-30}" stroke="{GRID}" stroke-width="1"/>')
        s.append(f'<text x="{x:.1f}" y="{altura-12}" fill="{MUTED}" font-size="12" text-anchor="middle">{v}%</text>')
    for i, (rot, val) in enumerate(dados):
        y = topo + i * alt_linha + 10
        w = util * val / maximo
        s.append(f'<text x="{esq-12}" y="{y+16}" fill="{INK}" font-size="14" text-anchor="end">{ESC(rot)}</text>')
        s.append(f'<path d="M{esq},{y} h{w-4:.1f} a4,4 0 0 1 4,4 v16 a4,4 0 0 1 -4,4 h-{w-4:.1f} z" fill="{BLUE}"/>')
        s.append(f'<text x="{esq+w+8:.1f}" y="{y+17}" fill="{INK}" font-size="14" font-weight="700">{str(val).replace(".", ",")}%</text>')
    s.append("</svg>")
    return f'<figure><figcaption class="tit">{ESC(titulo)}</figcaption>{"".join(s)}<figcaption class="fonte">Fonte: {ESC(fonte)}</figcaption></figure>'


def inclinacao():
    """Gráfico de inclinação 2015 → 2024: TEA x deficiência intelectual."""
    larg, alt = 640, 300
    x0, x1, topo, base = 120, 380, 30, 250
    y = lambda v: base - (base - topo) * v / 80
    series = [("Deficiência intelectual", 69.3, 48.5, AMBER, "4 3"), ("Autismo (TEA)", 5.6, 44.2, BLUE, "")]
    s = [f'<svg viewBox="0 0 {larg} {alt}" role="img" aria-label="Participação de TEA e deficiência intelectual nas matrículas da educação especial, 2015 e 2024" class="grafico">']
    for v in (0, 20, 40, 60, 80):
        s.append(f'<line x1="{x0-40}" y1="{y(v):.1f}" x2="{x1+40}" y2="{y(v):.1f}" stroke="{GRID}" stroke-width="1"/>')
    for ano, x in (("2015", x0), ("2024", x1)):
        s.append(f'<text x="{x}" y="{alt-18}" fill="{INK}" font-size="14" font-weight="700" text-anchor="middle">{ano}</text>')
    # rótulos da direita ficam perto (48,5 e 44,2): DI sobe, TEA desce
    desloc = {"Deficiência intelectual": -6, "Autismo (TEA)": 16}
    for nome, a, b, cor, traco in series:
        da = f' stroke-dasharray="{traco}"' if traco else ""
        s.append(f'<line x1="{x0}" y1="{y(a):.1f}" x2="{x1}" y2="{y(b):.1f}" stroke="{cor}" stroke-width="2.5"{da}/>')
        for x, v in ((x0, a), (x1, b)):
            s.append(f'<circle cx="{x}" cy="{y(v):.1f}" r="6" fill="{cor}" stroke="#fff" stroke-width="2"/>')
        s.append(f'<text x="{x0-14}" y="{y(a)+5:.1f}" fill="{INK}" font-size="13" text-anchor="end">{str(a).replace(".", ",")}%</text>')
        s.append(f'<text x="{x1+14}" y="{y(b)+desloc[nome]:.1f}" fill="{INK}" font-size="13" font-weight="700">{str(b).replace(".", ",")}% · {ESC(nome)}</text>')
    s.append("</svg>")
    legenda = ('<div class="legenda"><span><i style="background:%s"></i>Autismo (TEA), linha contínua</span>'
               '<span><i style="background:%s"></i>Deficiência intelectual, linha tracejada</span></div>') % (BLUE, AMBER)
    return ('<figure><figcaption class="tit">Quem são os estudantes da educação especial: participação nas matrículas</figcaption>'
            + legenda + "".join(s)
            + '<figcaption class="fonte">Fonte: Instituto Rodrigo Mendes, Panorama da Educação Especial 2025 (dados do Censo Escolar/INEP). '
              'Os demais tipos de deficiência e as altas habilidades completam o total e não aparecem no gráfico.</figcaption></figure>')


# ---------- blocos ----------
def evidencias(lista):
    li = "".join(
        f'<li><span class="tag tag-{e["tipo"]}">{SIMBOLO[e["tipo"]]} {ROTULO[e["tipo"]]}</span>'
        f'<span>{ESC(e["texto"])} <cite>{ESC(e["fonte"])}</cite></span></li>'
        for e in lista)
    return f'<ul class="evid">{li}</ul>'


def padrao(p):
    extras = ""
    if "niveis" in p:
        extras += '<dl class="niveis">' + "".join(
            f"<dt>Nível {k}</dt><dd>{ESC(v)}</dd>" for k, v in p["niveis"].items()) + "</dl>"
    if "parametros" in p:
        extras += '<table class="param"><tbody>' + "".join(
            f"<tr><th>{ESC(k.replace('_', ' ').capitalize())}</th><td>{ESC(v)}</td></tr>"
            for k, v in p["parametros"].items()) + "</tbody></table>"
    exemplos = ""
    if "exemplos" in p:
        exemplos = "<h4>Exemplos</h4><ul>" + "".join(f"<li>{ESC(x)}</li>" for x in p["exemplos"]) + "</ul>"
    return f'''
<section class="padrao">
  <header><span class="cod">{p["id"]}</span><h3>{ESC(p["nome"])}</h3></header>
  <p class="regra">{ESC(p["regra"])}</p>
  <div class="duas">
    <div>{exemplos}<h4>O que a plataforma faz</h4><ul>{"".join(f"<li>{ESC(x)}</li>" for x in p["como_a_plataforma_aplica"])}</ul>{extras}</div>
    <div><h4>Como conferir</h4><p>{ESC(p["verificacao"])}</p>
         <h4>Também ajuda</h4><p>{ESC(p["ajuda_tambem"])}</p></div>
  </div>
  <h4>Em que se baseia</h4>{evidencias(p["evidencias"])}
</section>'''


ICONES = {
    "sol": '<svg viewBox="0 0 40 40" class="ico"><circle cx="20" cy="20" r="8" fill="#C26A00"/><g stroke="#C26A00" stroke-width="3" stroke-linecap="round"><path d="M20 3v6M20 31v6M3 20h6M31 20h6M8 8l4 4M28 28l4 4M8 32l4-4M28 12l4-4"/></g></svg>',
    "nuvem": '<svg viewBox="0 0 40 40" class="ico"><path d="M12 30h17a7 7 0 0 0 0-14 10 10 0 0 0-19 3 6 6 0 0 0 2 11z" fill="#4A5668"/></svg>',
    "chuva": '<svg viewBox="0 0 40 40" class="ico"><path d="M12 22h17a7 7 0 0 0 0-14 10 10 0 0 0-19 3 6 6 0 0 0 2 11z" fill="#4A5668"/><g stroke="#1F5FBF" stroke-width="3" stroke-linecap="round"><path d="M14 27l-2 6M21 27l-2 6M28 27l-2 6"/></g></svg>',
    "ciclo": '<svg viewBox="0 0 40 40" class="ico"><g fill="none" stroke="#1F5FBF" stroke-width="3.5" stroke-linecap="round"><path d="M31 15a12 12 0 0 0-22 0"/><path d="M9 25a12 12 0 0 0 22 0"/></g><path d="M31 8v8h-8M9 32v-8h8" fill="none" stroke="#1F5FBF" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
}

TEXTO_ORIGINAL = ("O ciclo hidrológico consiste na circulação contínua da água entre a superfície terrestre e a atmosfera, "
                  "impulsionada pela energia solar. Ao ser aquecida, a água de oceanos, rios e lagos sofre evaporação; o vapor, "
                  "ao ascender e resfriar-se, condensa-se formando nuvens, que, saturadas, originam a precipitação.")
NIVEL_III = ("O ciclo da água é a circulação contínua da água entre a superfície da Terra e a atmosfera. "
             "A energia do Sol movimenta esse ciclo. O calor faz a água de oceanos, rios e lagos <b>evaporar</b>. "
             "O vapor sobe, esfria e se <b>condensa</b>: assim se formam as nuvens. Quando as nuvens ficam carregadas, "
             "a água cai. Isso se chama <b>precipitação</b>.")
NIVEL_II = ["A água da Terra está sempre em movimento.", "O Sol esquenta a água dos rios e do mar.",
            "A água vira vapor e sobe para o céu.", "Lá em cima, o vapor esfria e forma as nuvens.",
            "As nuvens ficam pesadas de água.", "Então a água cai. É a chuva.", "Depois, tudo começa de novo."]
NIVEL_I = [("sol", "O Sol esquenta a água."), ("nuvem", "A água sobe e vira nuvem."),
           ("chuva", "A nuvem solta a chuva."), ("ciclo", "E tudo começa de novo.")]


def exemplo_lf():
    ii = "".join(f"<span>{ESC(l)}</span>" for l in NIVEL_II)
    i = "".join(f'<div class="lf1">{ICONES[k]}<span>{ESC(t)}</span></div>' for k, t in NIVEL_I)
    return f'''
<div class="lf-grade">
  <div class="lf-caixa"><p class="lf-rot">Original · livro do 6º ano (exemplo criado pelo time)</p><p>{ESC(TEXTO_ORIGINAL)}</p></div>
  <div class="lf-caixa"><p class="lf-rot">Nível III · com glossário</p><p>{NIVEL_III}</p>
    <p class="glos"><b>evaporar</b>: virar vapor · <b>condensar</b>: o vapor voltar a ser gotinhas · <b>precipitação</b>: chuva, neve ou granizo</p></div>
  <div class="lf-caixa"><p class="lf-rot">Nível II · uma frase por linha</p><p class="linhas">{ii}</p></div>
  <div class="lf-caixa"><p class="lf-rot">Nível I · pouco texto, imagem de apoio</p>{i}</div>
</div>'''


def versoes():
    linhas = "".join(
        f'<tr><td><b>{ESC(v["nome"])}</b></td><td class="mono">{" ".join(v["aplica"])}</td><td>{ESC(v["para"])}</td></tr>'
        for v in P["versoes_geradas"])
    return f'<table class="tab"><thead><tr><th>Versão</th><th>Padrões</th><th>Para quem</th></tr></thead><tbody>{linhas}</tbody></table>'


FLUXO = [("Enviar", "O professor envia o material (PDF, texto ou imagem) e marca as necessidades da turma."),
         ("Analisar", "A plataforma encontra barreiras: informação só por cor, frases longas, páginas cheias, imagens sem descrição."),
         ("Transformar", "Aplica os padrões P1 a P6 e gera as versões: Universal, Ampliada, Leitura Fácil II e I, Áudio."),
         ("Revisar", "O professor confere, edita e aprova cada versão (P7). Nada é publicado sem ele."),
         ("Publicar", "O material fica salvo na biblioteca da turma. Cada aluno escolhe a versão que funciona melhor.")]


def fluxo():
    return '<ol class="fluxo">' + "".join(
        f'<li><span class="n">{i}</span><b>{ESC(t)}</b><span>{ESC(d)}</span></li>' for i, (t, d) in enumerate(FLUXO, 1)) + "</ol>"


# ---------- documento ----------
def documento(css_fontes):
    padroes_html = "".join(padrao(p) for p in P["padroes"])
    resumo = "".join(f'<li><span class="cod">{p["id"]}</span><b>{ESC(p["nome"])}</b><span>{ESC(p["regra"])}</span></li>' for p in P["padroes"])
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Manual Carcará de Materiais Acessíveis</title>
<style>{css_fontes}{CSS}</style></head><body>

<section class="capa">
  <p class="eyebrow">Carcará 3301 · versão {ESC(P["versao"])}</p>
  <h1>Manual de Materiais Acessíveis</h1>
  <p class="sub">Os padrões que a plataforma usa para transformar um material de aula em versões que toda a turma consegue usar. E em que pesquisas cada padrão se apoia.</p>
  <ul class="capa-leitores">
    <li><b>Professores e escolas</b><span>Partes 1 a 5: dados, princípios, funcionamento e os 7 padrões em detalhe.</span></li>
    <li><b>Famílias</b><span>Parte 6: o que a plataforma faz e como apoiar em casa, em linguagem simples.</span></li>
    <li><b>Estudantes</b><span>Parte 7: escrita em Leitura Fácil.</span></li>
  </ul>
  <p class="nota-capa">Este manual segue as próprias regras: fonte Atkinson Hyperlegible no texto (criada para leitores com baixa visão), Lexend nos títulos (criada para facilitar a leitura), linhas curtas e nenhuma informação passada só por cor.</p>
</section>

<section class="parte">
  <p class="eyebrow">Parte 1</p><h2>Por que este manual existe</h2>
  <p>Quase todos os estudantes com deficiência já estudam na mesma sala que os colegas. O desafio agora é que eles <b>aprendam</b> junto com a turma. Para isso, o material da aula precisa chegar a todos.</p>
  <div class="numeros">
    <div><b>2,07 milhões</b><span>matrículas na educação especial em 2024, contra 930 mil em 2015</span></div>
    <div><b>92,6%</b><span>dessas matrículas estão em classes comuns</span></div>
    <div><b>6,4%</b><span>dos professores regentes têm formação continuada em educação especial</span></div>
  </div>
  <p class="fonte-solta">Fonte dos três números: Instituto Rodrigo Mendes, Panorama da Educação Especial 2025, com dados do Censo Escolar/INEP.</p>
  {inclinacao()}
  <p>Autismo e deficiência intelectual concentram a maior parte das matrículas. Por isso os padrões P3 (Leitura Fácil), P5 (mais de um caminho) e P6 (estrutura previsível) são o centro da plataforma.</p>
  {barras_h("Pessoas com deficiência que frequentam a escola, por idade (2022)", [("6 a 14 anos", 95), ("15 a 17 anos", 84), ("18 a 24 anos", 24)], "IBGE, PNAD Contínua 2022, citada por Bacelar (2024)")}
  <p>A escola chega a quase todas as crianças com deficiência, mas elas vão ficando pelo caminho. Entre 18 e 24 anos, só uma em cada quatro ainda estuda.</p>
  <h3 class="h3s">O que os professores dizem</h3>
  <ul class="falas">
    <li>Falta tempo para planejar adaptações. É a principal queixa. <cite>Marques &amp; Duarte (2013)</cite></li>
    <li>Sentem angústia por uma formação que consideram insuficiente. <cite>Tavares, Santos &amp; Freitas (2016), 52 professores</cite></li>
    <li>Conhecem o PEI na teoria, mas não se sentem preparados para aplicá-lo. <cite>Santos (2024), 32 docentes</cite></li>
    <li>Sentem-se sozinhos e sem materiais adequados. <cite>Brito &amp; Flores (2023)</cite></li>
    <li>O ensino comum e a sala de recursos trabalham distantes um do outro. <cite>Moscardini (2011)</cite></li>
  </ul>
  <p>A plataforma ataca o problema do tempo: o professor envia o material uma vez, e as versões adaptadas saem prontas para ele revisar.</p>
</section>

<section class="parte">
  <p class="eyebrow">Parte 2</p><h2>Princípios</h2>
  <ol class="principios">
    <li><b>Universal primeiro.</b> A versão padrão de todo material já segue os padrões básicos. Ninguém precisa pedir para ter acesso. Domaredzki, Hummel &amp; Costa (2026) mostraram que o que é essencial para um aluno com deficiência foi benéfico para toda a turma.</li>
    <li><b>Mesmo conteúdo para todos.</b> Muda a forma, nunca o objetivo de aprendizagem.</li>
    <li><b>O aluno escolhe, sem rótulo.</b> As versões aparecem como opções ("prefiro ouvir", "texto mais direto"), nunca como "versão para deficientes".</li>
    <li><b>Necessidades, não diagnósticos.</b> A plataforma registra o que ajuda o aluno a aprender. Diagnóstico é tarefa de profissionais de saúde.</li>
    <li><b>Professor no comando.</b> A IA propõe; o professor decide.</li>
    <li><b>Transparência.</b> Todo material mostra quais padrões foram aplicados, e este manual mostra em que cada padrão se baseia.</li>
  </ol>
</section>

<section class="parte">
  <p class="eyebrow">Parte 3</p><h2>Como a plataforma funciona</h2>
  {fluxo()}
  <h3 class="h3s">As versões que a plataforma gera</h3>
  {versoes()}
</section>

<section class="parte">
  <p class="eyebrow">Parte 4</p><h2>Os 7 padrões de transformação</h2>
  <p>Cada padrão tem uma regra, o que a plataforma faz para cumpri-la, como conferir se deu certo e as evidências em que se apoia. As evidências estão marcadas pelo tipo:</p>
  <ul class="chave">
    <li><span class="tag tag-dados">● Dados</span> estudo com dados coletados</li>
    <li><span class="tag tag-pratica">◆ Prática</span> relato de prática, revisão ou estudo qualitativo</li>
    <li><span class="tag tag-norma">■ Norma</span> norma técnica ou lei</li>
    <li><span class="tag tag-projeto">○ Projeto</span> decisão do time, ainda a validar</li>
  </ul>
  <ul class="resumo">{resumo}</ul>
  {padroes_html}
  <div class="exemplo"><h3 class="h3s">Exemplo: o mesmo conteúdo em quatro níveis (P3 + P4)</h3>
  {exemplo_lf()}</div>
</section>

<section class="parte">
  <p class="eyebrow">Parte 5</p><h2>Limites e transparência</h2>
  <ul class="limites">
    <li><b>A plataforma não faz diagnóstico.</b> Se a família ou a escola notar dificuldades persistentes, o caminho é procurar a equipe da escola e um profissional de saúde.</li>
    <li><b>A IA pode errar.</b> Uma simplificação pode mudar o sentido de um conceito. Por isso nenhuma versão é publicada sem a revisão do professor (P7).</li>
    <li><b>Não substitui pessoas.</b> O Atendimento Educacional Especializado (AEE), o intérprete de Libras, o professor de apoio e a transcrição profissional em braile continuam necessários.</li>
    <li><b>Recolorir imagens não serve para todos</b> os tipos de daltonismo (Bacelar, 2024). Por isso a regra principal é acrescentar símbolos e rótulos, não trocar cores.</li>
    <li><b>Muitas evidências vêm de estudos pequenos</b> e qualitativos. Os parâmetros marcados como ○ Projeto precisam ser testados com alunos e professores.</li>
    <li><b>Alguns números são de fontes secundárias</b> e serão conferidos nas bases oficiais do INEP e do IBGE.</li>
  </ul>
</section>

<section class="parte familia">
  <p class="eyebrow">Parte 6 · Para famílias</p><h2>O que a plataforma faz pelo seu filho ou filha</h2>
  <p>O professor coloca o material da aula na plataforma. A plataforma prepara versões diferentes do mesmo conteúdo. Por exemplo: letras maiores, um texto mais direto ou um áudio.</p>
  <p>Seu filho ou filha escolhe a versão que funciona melhor. Todos os colegas podem usar as mesmas versões. Ninguém é separado.</p>
  <h3 class="h3s">Como apoiar em casa</h3>
  <ul>
    <li>Peça para a criança mostrar qual versão ela prefere e por quê.</li>
    <li>Leiam juntos a versão em Leitura Fácil antes de uma prova.</li>
    <li>Use o áudio em momentos fora da tela, como no caminho para a escola.</li>
    <li>Conte ao professor o que funciona em casa. Essa informação ajuda a escolher as próximas adaptações.</li>
  </ul>
  <h3 class="h3s">Perguntas que você pode fazer à escola</h3>
  <ul>
    <li>Meu filho ou filha tem um Plano Educacional Individualizado (PEI)? Posso participar?</li>
    <li>Há Atendimento Educacional Especializado (AEE) na escola?</li>
    <li>Como vocês vão avaliar o que ele ou ela aprendeu?</li>
  </ul>
  <p class="aviso">A plataforma nunca diz se uma criança tem uma deficiência. Se você tem dúvidas sobre o desenvolvimento do seu filho ou filha, converse com a escola e procure um profissional de saúde.</p>
</section>

<section class="parte estudante">
  <p class="eyebrow">Parte 7 · Para estudantes</p><h2>Este site é seu também</h2>
  <p class="linhas"><span>Aqui ficam os materiais da sua turma.</span><span>Cada material tem jeitos diferentes de estudar.</span><span>Você pode ler com letras grandes.</span><span>Você pode ler um texto mais curto.</span><span>Você pode ouvir.</span><span>Você escolhe o jeito que é melhor para você.</span><span>Pode trocar de jeito quando quiser.</span><span>Se algo estiver difícil, fale com o seu professor.</span></p>
</section>

<section class="parte refs">
  <p class="eyebrow">Referências</p><h2>Fontes usadas neste manual</h2>
  <ol>{REFS}</ol>
</section>
</body></html>'''


REFS = "".join(f"<li>{r}</li>" for r in [
    "ALONSO, S. A. N.; SOUZA, J. L. O uso de tecnologias digitais e tecnologia assistiva no Desenho Universal para Aprendizagem na educação inclusiva de estudantes com autismo. <i>South American Journal of Basic Education, Technical and Technological</i>, v. 12, supl. 2, 2026.",
    "ALVES, A. L. C.; ALVES, P. S. R. Daltonismo no ambiente educacional: desafios, percepções e estratégias de inclusão. Centro Universitário de Volta Redonda (UniFOA), 2025.",
    "BACELAR, C. C. <i>Pesquisa e inovações sobre tecnologias assistivas: recursos educacionais da UNA-SUS/UFMA para daltônicos</i>. Dissertação (Mestrado em Design), UFMA, 2024.",
    "BRASIL. Lei nº 13.146, de 6 de julho de 2015 (Lei Brasileira de Inclusão).",
    "BRASIL. Lei nº 13.709, de 14 de agosto de 2018 (Lei Geral de Proteção de Dados).",
    "BRITO, G. A.; FLORES, M. M. L. A inclusão de alunos com deficiência intelectual: em foco as práticas pedagógicas. <i>Boletim de Conjuntura (BOCA)</i>, v. 16, n. 48, 2023.",
    "CAMPOS, G. G. G. <i>O uso da linguagem simples como ferramenta de inclusão para pessoas com deficiência intelectual</i>. TCC (Pedagogia), UFRN, 2023.",
    "CARVALHO, K. P. G. et al. O Plano Educacional Individualizado (PEI) e os desafios gerados pela falta de formação continuada para professores. <i>REASE</i>, v. 12, n. 6, 2026.",
    "COSTA, R. C. M. et al. A acessibilidade de pessoas com daltonismo: a construção de um protótipo de AVA inclusivo. <i>Informática na Educação: teoria &amp; prática</i>, v. 20, n. 2, 2017.",
    "DOMAREDZKI, A. B.; HUMMEL, E. I.; COSTA, P. K. A. Tecnologia assistiva educacional como recurso no planejamento do Desenho Universal para Aprendizagem. <i>Revista Educação Especial</i>, v. 38, 2025 (publicado em 2026).",
    "INSTITUTO RODRIGO MENDES. <i>Panorama da Educação Especial 2025</i>. São Paulo, 2026.",
    "MARQUES, A.; DUARTE, M. O trabalho colaborativo: uma estratégia de ensino na aprendizagem de alunos com deficiência intelectual. <i>Revista de Ciências Humanas</i>, v. 14, n. 23, 2013.",
    "MOSCARDINI, S. F. <i>Escolarização de alunos com deficiência intelectual em classes comuns e em salas de recursos multifuncionais</i>. Dissertação (Mestrado), UNESP Araraquara, 2011.",
    "MUÑOZ, Ó. G. <i>Lectura fácil: métodos de redacción y evaluación</i>. Madri, 2012. (citado por Pires &amp; Machado e por Souza, Campos &amp; Carrizalez)",
    "PIRES, V. O. D.; MACHADO, V. P. Adaptação textual para pessoas com deficiência intelectual: uma proposta de mediação pedagógica. 2021.",
    "SANTOS, J. C. <i>A prática do professor na elaboração de um Plano Educacional Individualizado (PEI) para alunos em sala de aula inclusiva, no Rio de Janeiro</i>. Dissertação (Mestrado em Ciências da Educação), 2024.",
    "SILVA, G. L.; CAMARGO, S. P. H. Revisão integrativa da produção científica nacional sobre o Plano Educacional Individualizado. <i>Revista Educação Especial</i>, v. 34, 2021.",
    "SILVA, T. M. <i>Desenho Universal na Aprendizagem e autoscopia: formação continuada docente para a inclusão escolar de alunos com TEA</i>. Tese (Doutorado em Educação), UERJ, 2022.",
    "SOUZA, C. S. M.; CAMPOS, R. H. F.; CARRIZALEZ, D. M. La lectura fácil como estrategia de accesibilidad cognitiva para la educación inclusiva de estudiantes con discapacidad intelectual. <i>Revista Saber Incluir</i> (ano a confirmar).",
    "TAVARES, L. M. F. L.; SANTOS, L. M. M.; FREITAS, M. N. C. A educação inclusiva: um estudo sobre a formação docente. <i>Revista Brasileira de Educação Especial</i>, v. 22, 2016.",
    "TSUCHIYA, A. M. <i>O Desenho Universal da Aprendizagem e o estudante com Transtorno do Espectro Autista</i>. TCC (Pedagogia), UNESP Bauru, 2022.",
    "W3C. <i>Web Content Accessibility Guidelines (WCAG) 2.2</i>. 2023.",
])

CSS = """
@page { size: A4; }
:root { --ink:#142033; --muted:#4A5668; --line:#D8DEE6; --soft:#EEF2F7; --blue:#1F5FBF; --amber:#C26A00;
  --display:'Lexend',system-ui,sans-serif; --body:'Atkinson Hyperlegible',system-ui,sans-serif; --mono:'IBM Plex Mono',ui-monospace,monospace; }
* { box-sizing:border-box }
body { margin:0; color:var(--ink); background:#fff; font:11.5pt/1.55 var(--body); }
h1,h2,h3,h4 { font-family:var(--display); line-height:1.2; margin:0; text-wrap:balance; }
h2 { font-size:22pt; font-weight:600; margin-bottom:10pt; }
h3 { font-size:15pt; font-weight:600; }
.h3s { margin:16pt 0 6pt; }
h4 { font-size:10pt; font-weight:600; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); margin:10pt 0 4pt; }
p { margin:0 0 8pt; max-width:62ch; }
ul,ol { margin:0 0 8pt; padding-left:16pt; }
li { margin-bottom:3pt; }
cite { font-style:normal; color:var(--muted); font-size:9.5pt; }
.eyebrow { font-family:var(--mono); font-size:9pt; letter-spacing:.08em; text-transform:uppercase; color:var(--blue); margin-bottom:4pt; }
.mono { font-family:var(--mono); }
.capa { min-height:250mm; display:flex; flex-direction:column; justify-content:center; break-after:page; border-left:6pt solid var(--blue); padding-left:18pt; }
.capa h1 { font-size:38pt; font-weight:700; letter-spacing:-.01em; margin:6pt 0 14pt; max-width:14ch; }
.capa .sub { font-size:14pt; max-width:40ch; }
.capa-leitores { list-style:none; padding:0; margin:20pt 0; display:grid; gap:8pt; }
.capa-leitores li { display:grid; grid-template-columns:42mm 1fr; gap:8pt; padding:8pt 0; border-top:1px solid var(--line); }
.capa-leitores b { font-family:var(--display); font-weight:600; }
.nota-capa { font-size:9.5pt; color:var(--muted); max-width:70ch; }
.parte { break-before:page; }
.parte:nth-of-type(2) { break-before:auto; }
.numeros { display:grid; grid-template-columns:repeat(3,1fr); gap:10pt; margin:12pt 0 4pt; }
.numeros div { border-top:3pt solid var(--ink); padding-top:6pt; }
.numeros b { display:block; font-family:var(--display); font-size:22pt; font-weight:700; font-variant-numeric:tabular-nums; }
.numeros span { font-size:10pt; color:var(--muted); }
.fonte-solta { font-size:9pt; color:var(--muted); }
figure { margin:14pt 0; break-inside:avoid; }
.grafico { width:100%; height:auto; font-family:var(--body); }
figcaption.tit { font-family:var(--display); font-weight:600; font-size:11.5pt; margin-bottom:4pt; }
figcaption.fonte { font-size:8.5pt; color:var(--muted); margin-top:2pt; }
.legenda { display:flex; gap:16pt; font-size:9.5pt; margin:2pt 0 4pt; }
.legenda i { display:inline-block; width:14pt; height:4pt; border-radius:2pt; margin-right:5pt; vertical-align:middle; }
.falas { list-style:none; padding:0; }
.falas li { padding:5pt 0 5pt 12pt; border-left:2pt solid var(--line); margin-bottom:6pt; }
.falas cite { display:block; }
.principios li { margin-bottom:7pt; }
.fluxo { list-style:none; padding:0; display:grid; gap:0; }
.fluxo li { display:grid; grid-template-columns:24pt 26mm 1fr; gap:8pt; align-items:baseline; padding:8pt 0; border-top:1px solid var(--line); }
.fluxo .n { font-family:var(--mono); font-weight:500; color:var(--blue); }
.fluxo b { font-family:var(--display); font-weight:600; }
.tab { width:100%; border-collapse:collapse; font-size:10pt; }
.tab th { text-align:left; font-family:var(--display); font-weight:600; border-bottom:1.5pt solid var(--ink); padding:4pt 6pt 4pt 0; }
.tab td { border-bottom:1px solid var(--line); padding:5pt 6pt 5pt 0; vertical-align:top; }
.chave { list-style:none; padding:0; display:grid; grid-template-columns:1fr 1fr; gap:4pt 14pt; font-size:10pt; }
.tag { display:inline-block; font-family:var(--mono); font-size:8pt; letter-spacing:.04em; text-transform:uppercase; padding:1pt 5pt; border:1px solid var(--ink); border-radius:3pt; white-space:nowrap; }
.tag-dados { background:var(--ink); color:#fff; }
.tag-pratica { background:#fff; }
.tag-norma { background:var(--soft); }
.tag-projeto { border-style:dashed; color:var(--muted); border-color:var(--muted); }
.resumo { list-style:none; padding:0; margin:12pt 0 4pt; }
.resumo li { display:grid; grid-template-columns:20pt 42mm 1fr; gap:8pt; padding:6pt 0; border-top:1px solid var(--line); font-size:10pt; }
.cod { font-family:var(--mono); font-weight:500; color:var(--blue); }
.padrao { break-before:page; }
.padrao header { display:flex; align-items:baseline; gap:10pt; border-bottom:2pt solid var(--ink); padding-bottom:6pt; margin-bottom:8pt; }
.padrao header .cod { font-size:26pt; }
.padrao h3 { font-size:20pt; }
.regra { font-family:var(--display); font-size:13pt; font-weight:500; max-width:52ch; }
.duas { display:grid; grid-template-columns:1.25fr 1fr; gap:16pt; }
.duas > div:last-child { background:var(--soft); padding:4pt 10pt 8pt; border-radius:4pt; }
.duas ul { font-size:10.5pt; }
.niveis { display:grid; grid-template-columns:auto 1fr; gap:3pt 8pt; font-size:10pt; margin:6pt 0; }
.niveis dt { font-family:var(--mono); font-weight:500; }
.niveis dd { margin:0; }
.param { border-collapse:collapse; font-size:9.5pt; margin-top:6pt; }
.param th { text-align:left; font-weight:400; color:var(--muted); padding:2pt 10pt 2pt 0; }
.param td { padding:2pt 0; font-weight:700; }
.evid { list-style:none; padding:0; font-size:10pt; }
.evid li { display:grid; grid-template-columns:22mm 1fr; gap:8pt; padding:5pt 0; border-top:1px solid var(--line); break-inside:avoid; }
.evid cite { display:block; }
.lf-grade { display:grid; grid-template-columns:1fr 1fr; gap:10pt; break-inside:avoid; }
.lf-caixa { border:1px solid var(--line); border-radius:4pt; padding:8pt 10pt; font-size:10.5pt; }
.lf-rot { font-family:var(--mono); font-size:8.5pt; text-transform:uppercase; letter-spacing:.05em; color:var(--blue); margin-bottom:4pt; }
.linhas span { display:block; }
.glos { font-size:9pt; color:var(--muted); border-top:1px dashed var(--line); padding-top:4pt; }
.lf1 { display:flex; align-items:center; gap:8pt; margin-bottom:5pt; font-size:12pt; }
.ico { width:26pt; height:26pt; flex:none; }
.exemplo { break-before:page; }
.limites li { margin-bottom:7pt; }
.familia p, .familia li { font-size:12.5pt; }
.aviso { border:1.5pt solid var(--ink); border-radius:4pt; padding:8pt 10pt; margin-top:12pt; }
.estudante .linhas { font-size:16pt; line-height:1.7; }
.refs ol { font-size:9.5pt; padding-left:14pt; }
.refs li { margin-bottom:5pt; }
"""


def css_fontes(pasta: Path | None) -> str:
    if not pasta:
        return ('@import url("https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400'
                '&family=IBM+Plex+Mono:wght@400;500&family=Lexend:wght@400;500;600;700&display=swap");')
    def face(fam, arq, peso="400", estilo="normal"):
        b64 = base64.b64encode((pasta / arq).read_bytes()).decode()
        return (f"@font-face{{font-family:'{fam}';src:url(data:font/ttf;base64,{b64}) format('truetype');"
                f"font-weight:{peso};font-style:{estilo};}}")
    return "".join([
        face("Atkinson Hyperlegible", "AtkinsonHyperlegible-Regular.ttf"),
        face("Atkinson Hyperlegible", "AtkinsonHyperlegible-Bold.ttf", "700"),
        face("Atkinson Hyperlegible", "AtkinsonHyperlegible-Italic.ttf", "400", "italic"),
        face("Lexend", "Lexend[wght].ttf", "100 900"),
        face("IBM Plex Mono", "IBMPlexMono-Regular.ttf"),
        face("IBM Plex Mono", "IBMPlexMono-Medium.ttf", "500"),
    ])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fontes", type=Path, help="pasta com os .ttf (embute as fontes no PDF)")
    ap.add_argument("--sem-pdf", action="store_true")
    a = ap.parse_args()
    (AQUI / "manual.html").write_text(documento(css_fontes(None)), encoding="utf-8")
    if a.sem_pdf:
        return
    from playwright.sync_api import sync_playwright
    tmp = AQUI / "_manual_pdf.html"
    tmp.write_text(documento(css_fontes(a.fontes)), encoding="utf-8")
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        pg = nav.new_page()
        pg.goto(tmp.resolve().as_uri())
        pg.wait_for_timeout(400)
        pg.pdf(path=str(AQUI / "manual-carcara-v0.1.pdf"), format="A4", print_background=True,
               display_header_footer=True, header_template="<span></span>",
               footer_template='<div style="width:100%;font:8px sans-serif;color:#4A5668;padding:0 18mm;display:flex;justify-content:space-between">'
                               '<span>Manual de Materiais Acessíveis · Carcará 3301 · v0.1</span><span class="pageNumber"></span></div>',
               margin={"top": "18mm", "bottom": "20mm", "left": "18mm", "right": "18mm"})
        nav.close()
    tmp.unlink()


if __name__ == "__main__":
    main()
