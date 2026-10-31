"""Gera o Plano de Negócio do PRISMA em PDF, no formato de slides 16:9, a partir do modelo (modelo.py) e dos dados do manual.

Uso:  python pitch/plano-negocio/gerar_pdf.py
Saída: pitch/plano-negocio/plano-de-negocio-prisma.pdf   (e o .html, para conferir no navegador)
Precisa do pacote playwright (pip install playwright). Usa o Microsoft Edge já instalado no Windows;
em outro sistema, troque CANAL para None e rode "python -m playwright install chromium".
"""
from __future__ import annotations

import base64
import html
import importlib.util
import math
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(AQUI))
import modelo as M  # noqa: E402

# os gráficos do próprio manual (mesmas funções e mesmos dados de docs/manual/padroes.json)
_spec = importlib.util.spec_from_file_location("build_manual", RAIZ / "docs" / "manual" / "build_manual.py")
BM = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(BM)
DADOS_MANUAL = BM.D["dados"]

CANAL = "msedge"
ESC = html.escape
INK, MUTED, GRID, AZUL, LARANJA, SOFT = "#1E2235", "#4A4F6A", "#D9D3C4", "#1F6FB2", "#A3401F", "#F3EDDF"
br = M.br
R = M.resumo()
P = R["publico"]
MESES_NOME = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def mi(x, casas=1):
    return f"{br(x / 1e6, casas)} mi"


def reais(x, casas=0):
    return f"R$ {br(x, casas)}"


def mes_ano(l):
    return f"{MESES_NOME[l['mes'] - 1]}/{l['ano']}"


# ---------------- fontes do site (números nunca na fonte pixel) ----------------
def fontes():
    def face(fam, arq, peso="400", extra=""):
        b64 = base64.b64encode((RAIZ / "web" / "assets" / "fontes" / arq).read_bytes()).decode()
        return f"@font-face{{font-family:'{fam}';src:url(data:font/woff2;base64,{b64}) format('woff2');font-weight:{peso};{extra}}}"
    sem_digitos = "unicode-range:U+0000-002F,U+003A-10FFFF;"
    return "".join([face("Atkinson Hyperlegible Next", "atkinson-400.woff2"),
                    face("Atkinson Hyperlegible Next", "atkinson-700.woff2", "700"),
                    face("Pixelify Sans", "pixelify-400.woff2", "400", sem_digitos),
                    face("Departure Mono", "departure-mono.woff2")])


# ---------------- gráficos novos (mesmo desenho do manual: barras com contorno de tinta) ----------------
def colunas(titulo, itens, fonte, fmt, largura=640, altura=250, cor=AZUL):
    topo, base, esq = 30, 40, 20
    util_h = altura - topo - base
    maximo = max(v for _, v in itens) * 1.12
    passo = (largura - 2 * esq) / len(itens)
    s = [f'<svg viewBox="0 0 {largura} {altura}" class="grafico" role="img" aria-label="{ESC(titulo)}">',
         f'<line x1="{esq}" y1="{altura - base}" x2="{largura - esq}" y2="{altura - base}" stroke="{INK}" stroke-width="2"/>']
    for i, (rot, v) in enumerate(itens):
        h = util_h * v / maximo
        x = esq + i * passo + passo * 0.25
        w = passo * 0.5
        y = altura - base - h
        s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{cor}" stroke="{INK}" stroke-width="2"/>')
        s.append(f'<text x="{x + w / 2:.1f}" y="{y - 8:.1f}" text-anchor="middle" font-size="15" font-weight="700" fill="{INK}">{ESC(fmt(v))}</text>')
        s.append(f'<text x="{x + w / 2:.1f}" y="{altura - base + 22}" text-anchor="middle" font-size="14" fill="{INK}">{ESC(rot)}</text>')
    s.append("</svg>")
    return f'<figure><figcaption class="tit">{ESC(titulo)}</figcaption>{"".join(s)}<figcaption class="fonte">Fonte: {ESC(fonte)}</figcaption></figure>'


def barras_duplas(titulo, grupos, series, fonte, largura=640, altura=260):
    """grupos: [(rótulo, [v1, v2])]; series: [(nome, cor)]. Valores em %."""
    topo, base, esq = 34, 46, 46
    util_h, util_w = altura - topo - base, largura - esq - 20
    s = [f'<svg viewBox="0 0 {largura} {altura}" class="grafico" role="img" aria-label="{ESC(titulo)}">']
    for k in range(5):
        y = altura - base - util_h * k / 4
        s.append(f'<line x1="{esq}" y1="{y:.1f}" x2="{largura - 20}" y2="{y:.1f}" stroke="{GRID}"/>')
        s.append(f'<text x="{esq - 8}" y="{y + 4:.1f}" text-anchor="end" font-size="12" fill="{MUTED}">{25 * k}%</text>')
    passo = util_w / len(grupos)
    larg = passo * 0.28
    for i, (rot, vals) in enumerate(grupos):
        x0 = esq + i * passo + passo * 0.18
        for j, v in enumerate(vals):
            h = util_h * v / 100
            x = x0 + j * (larg + 4)
            y = altura - base - h
            s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{larg:.1f}" height="{h:.1f}" fill="{series[j][1]}" stroke="{INK}" stroke-width="2"/>')
            s.append(f'<text x="{x + larg / 2:.1f}" y="{y - 7:.1f}" text-anchor="middle" font-size="14" font-weight="700" fill="{INK}">{br(v, 1)}%</text>')
        s.append(f'<text x="{x0 + larg + 2:.1f}" y="{altura - base + 22}" text-anchor="middle" font-size="14" fill="{INK}">{ESC(rot)}</text>')
    s.append("</svg>")
    leg = "".join(f'<li><i style="background:{c}"></i>{ESC(n)}</li>' for n, c in series)
    return (f'<figure><figcaption class="tit">{ESC(titulo)}</figcaption><ul class="legenda">{leg}</ul>{"".join(s)}'
            f'<figcaption class="fonte">Fonte: {ESC(fonte)}</figcaption></figure>')


def passo_redondo(intervalo, n=4):
    """Passo de eixo "redondo" (1, 2, 2,5 ou 5 × 10^k), para o eixo não mostrar valores quebrados."""
    bruto = intervalo / n
    p = 10 ** math.floor(math.log10(bruto))
    return next(m * p for m in (1, 2, 2.5, 5, 10) if m * p >= bruto)


def dinheiro_curto(v):
    a, sinal = abs(v), ("−" if v < 0 else "")
    if a < 0.5:
        return "R$ 0"
    if a >= 1e6:
        return f"{sinal}R$ {br(a / 1e6, 1)} mi"
    return f"{sinal}R$ {br(a / 1e3)} mil"


def linhas(titulo, series, fonte, marcar=None, largura=640, altura=270, zero=False, fmt=dinheiro_curto):
    """series: [(nome, cor, [valores mensais])]. Um só eixo (reais por mês)."""
    topo, base, esq, dir_ = 24, 40, 78, 130
    util_h, util_w = altura - topo - base, largura - esq - dir_
    todos = [v for _, _, vs in series for v in vs]
    passo = passo_redondo(max(todos) - min(0, min(todos)))
    lo = math.floor(min(0, min(todos)) / passo) * passo
    hi = math.ceil(max(todos) * 1.04 / passo) * passo
    n = len(series[0][2])
    X = lambda i: esq + util_w * i / (n - 1)
    Y = lambda v: topo + util_h * (hi - v) / (hi - lo)
    s = [f'<svg viewBox="0 0 {largura} {altura}" class="grafico" role="img" aria-label="{ESC(titulo)}">']
    v = lo
    while v <= hi + passo / 2:
        s.append(f'<line x1="{esq}" y1="{Y(v):.1f}" x2="{esq + util_w}" y2="{Y(v):.1f}" stroke="{GRID}"/>')
        s.append(f'<text x="{esq - 8}" y="{Y(v) + 4:.1f}" text-anchor="end" font-size="11" fill="{MUTED}">{ESC(fmt(v))}</text>')
        v += passo
    if zero and lo < 0:
        s.append(f'<line x1="{esq}" y1="{Y(0):.1f}" x2="{esq + util_w}" y2="{Y(0):.1f}" stroke="{INK}" stroke-width="1.5"/>')
    for a in range(0, n, 12):
        s.append(f'<line x1="{X(a):.1f}" y1="{topo}" x2="{X(a):.1f}" y2="{topo + util_h}" stroke="{GRID}" stroke-dasharray="3 3"/>')
        s.append(f'<text x="{X(a) + 4:.1f}" y="{altura - 14}" font-size="12" fill="{MUTED}">jan/{M.INICIO_ANO + a // 12}</text>')
    if marcar:
        i, rot = marcar
        s.append(f'<line x1="{X(i):.1f}" y1="{topo}" x2="{X(i):.1f}" y2="{topo + util_h}" stroke="{INK}" stroke-width="2" stroke-dasharray="6 4"/>')
        s.append(f'<text x="{X(i) - 6:.1f}" y="{topo + 14}" text-anchor="end" font-size="12" font-weight="700" fill="{INK}">{ESC(rot)}</text>')
    for nome, cor, vs in series:
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(vs))
        s.append(f'<polyline points="{pts}" fill="none" stroke="{cor}" stroke-width="3" stroke-linejoin="round"/>')
        s.append(f'<circle cx="{X(n - 1):.1f}" cy="{Y(vs[-1]):.1f}" r="4.5" fill="{cor}" stroke="{INK}" stroke-width="1.5"/>')
        s.append(f'<text x="{X(n - 1) + 10:.1f}" y="{Y(vs[-1]) + 5:.1f}" font-size="13" font-weight="700" fill="{INK}">{ESC(nome)}</text>')
    s.append("</svg>")
    leg = "".join(f'<li><i style="background:{c}"></i>{ESC(nm)}</li>' for nm, c, _ in series) if len(series) > 1 else ""
    return (f'<figure><figcaption class="tit">{ESC(titulo)}</figcaption>{"<ul class=legenda>" + leg + "</ul>" if leg else ""}'
            f'{"".join(s)}<figcaption class="fonte">Fonte: {ESC(fonte)}</figcaption></figure>')


def funil():
    itens = [
        ("Todos os alunos do fundamental", P["ef"], "se beneficiam das versões (desenho universal)"),
        ("Com dificuldade de leitura", P["dificuldade"], f"{br(100 * P['sem_lp'])}% sem aprendizado adequado em português (Saeb 2025)"),
        ("Com necessidade específica", P["nucleo"], "deficiência, autismo, TDAH, dislexia ou daltonismo (estimativa)"),
        ("Na rede particular", P["privada"], f"{br(V['escolas_ef_privadas'])} escolas: nosso primeiro mercado"),
    ]
    larg, alt_l = 640, 64
    s = [f'<svg viewBox="0 0 {larg} {alt_l * len(itens) + 6}" class="grafico" role="img" aria-label="Funil de alunos">']
    for i, (rot, v, nota) in enumerate(itens):
        w = max((larg - 4) * v / P["ef"], 40)
        y = i * alt_l + 2
        # rótulo em cima da barra (nunca é cortado); número dentro da barra, com contraste
        cor, cor_num = [(AZUL, "#FFFFFF"), ("#4E8CC4", INK), ("#9DBEDF", INK), (LARANJA, "#FFFFFF")][i]
        s.append(f'<text x="2" y="{y + 15}" font-size="14" fill="{INK}"><tspan font-weight="700">{ESC(rot)}</tspan>'
                 f'<tspan fill="{MUTED}" font-size="12"> · {ESC(nota)}</tspan></text>')
        s.append(f'<rect x="2" y="{y + 22}" width="{w:.1f}" height="32" fill="{cor}" stroke="{INK}" stroke-width="2"/>')
        s.append(f'<text x="12" y="{y + 44}" font-size="16" font-weight="700" fill="{cor_num}">{mi(v)}</text>')
    s.append("</svg>")
    return s


V = M.V


def figura_funil():
    s = funil()
    # rótulos longos: o funil vira barras alinhadas à esquerda, com o texto ao lado (mais legível que um trapézio)
    return ('<figure><figcaption class="tit">Quantos alunos o PRISMA alcança (ensino fundamental)</figcaption>'
            f'{"".join(s)}<figcaption class="fonte">Fontes: INEP, Censo Escolar 2025; Saeb 2025 (Todos Pela Educação); '
            'estimativa do time para necessidades específicas (seção Quem precisa). As faixas se sobrepõem: cada uma está contida na anterior, '
            'menos a rede particular, que é um recorte de todos os alunos.</figcaption></figure>')


# ---------------- conteúdo ----------------
PL = R["planos"]
VAL = R["valor"]
EQ = R["equilibrio"]
CEN = R["cenarios"]
APORTE = 500_000
LIN = R["linhas"]


def tabela_planos():
    linhas_ = "".join(
        f"<tr><td><b>{x['nome']}</b><span class='sub'>{x['faixa']}</span></td><td class='num'>{reais(x['anual'])}</td>"
        f"<td class='num'>{reais(x['semestre'])}</td><td class='num'>{reais(x['mes_equivalente'])}</td>"
        f"<td class='num'>{reais(x['por_aluno_ano_ref'])} com {x['ref']} alunos"
        f"<span class='sub'>{reais(x['anual'] / int(x['faixa'].split()[-2].replace('.', '')))} com {x['faixa'].split()[-2]}</span></td></tr>"
        for x in PL.values())
    return ("<table class='t'><thead><tr><th>Plano</th><th>Anual</th><th>Semestral</th><th>Equivale por mês</th>"
            "<th>Por aluno por ano</th></tr></thead><tbody>" + linhas_ +
            "<tr><td><b>Redes e escolas maiores</b><span class='sub'>acima de 1.000 alunos</span></td>"
            "<td colspan='4'>Proposta sob medida, a partir de R$ 45 por aluno por ano.</td></tr></tbody></table>")


def tabela_anos():
    corpo = "".join(
        f"<tr><td>{a['ano']}</td><td class='num'>{br(a['escolas_fim'])}</td><td class='num'>{reais(a['receita'])}</td>"
        f"<td class='num'>{reais(a['custo'])}</td><td class='num {'neg' if a['resultado'] < 0 else ''}'>{reais(a['resultado'])}</td>"
        f"<td class='num'>{reais(a['arr_fim'])}</td></tr>" for a in R["anos"])
    return ("<table class='t'><thead><tr><th>Ano</th><th>Escolas no fim do ano</th><th>Receita no ano</th><th>Custos no ano</th>"
            "<th>Resultado</th><th>Receita anual recorrente em dezembro</th></tr></thead><tbody>" + corpo + "</tbody></table>")


def tabela_cenarios():
    nomes = {"pessimista": "Pessimista", "base": "Base", "otimista": "Otimista"}
    desc = {"pessimista": "40% menos vendas, 50% mais cancelamentos e aquisição 50% mais cara",
            "base": "as hipóteses da seção Projeção", "otimista": "40% mais vendas, 30% menos cancelamentos e aquisição 20% mais barata"}
    corpo = ""
    for k in ("pessimista", "base", "otimista"):
        c = CEN[k]
        e = c["equilibrio"]
        corpo += (f"<tr><td><b>{nomes[k]}</b><span class='sub'>{desc[k]}</span></td><td class='num'>{br(c['escolas_fim'])}</td>"
                  f"<td class='num'>{reais(c['arr_fim'])}</td><td class='num'>{mes_ano(e) if e else 'depois de 2029'}</td>"
                  f"<td class='num'>{reais(c['investimento'])}</td></tr>")
    return ("<table class='t'><thead><tr><th>Cenário</th><th>Escolas em dez/2029</th><th>Receita anual recorrente</th>"
            "<th>Lucro todo mês a partir de</th><th>Dinheiro necessário até lá</th></tr></thead><tbody>" + corpo + "</tbody></table>")


def tabela_marcos():
    o_que = {
        6: "3 escolas do piloto viram clientes; horas economizadas medidas e publicadas",
        12: "Primeiro ciclo completo de vendas; taxa de conversão do teste grátis conhecida",
        18: "Vendedor e pessoa de suporte contratados; segunda temporada de vendas",
        24: "Plataforma pronta para redes públicas (primeiro contato com prefeituras)",
        36: "Lucro todo mês; pronto para a rodada seguinte ou para crescer só com o caixa",
    }
    corpo = "".join(
        f"<tr><td>{mes_ano(LIN[m - 1])}</td><td class='num'>{br(LIN[m - 1]['ativas'])}</td>"
        f"<td class='num'>{reais(LIN[m - 1]['receita'] * 12)}</td><td>{ESC(t)}</td></tr>" for m, t in o_que.items())
    return ("<table class='t'><thead><tr><th>Quando</th><th>Escolas pagando</th><th>Receita anual recorrente</th>"
            "<th>O que precisa ser verdade</th></tr></thead><tbody>" + corpo + "</tbody></table>")


def uso_recursos():
    fim = R["pior_mes"]["m"]
    tot = {}
    for l in LIN[:fim]:
        for k, v in l["detalhe"].items():
            tot[k] = tot.get(k, 0) + v
    soma = sum(tot.values())
    itens = sorted(((k, 100 * v / soma) for k, v in tot.items()), key=lambda x: -x[1])
    return BM.barras_h(f"Para onde vai o dinheiro até o pior momento de caixa ({mes_ano(R['pior_mes'])})", itens,
                       "modelo do time (modelo.py), cenário base", maximo=60, esq=210)


def fontes_lista():
    vistos, itens = set(), []
    for chave, (_, fonte) in M.DADOS.items():
        if fonte not in vistos:
            vistos.add(fonte)
            itens.append(fonte)
    itens += [
        "Instituto Rodrigo Mendes, Panorama da Educação Especial 2025 (Censo Escolar/INEP 2024): registros por tipo, formação de professores, escolas sem acessibilidade",
        "IBGE, PNAD Contínua 2022, citada por Bacelar (UFMA, 2024): pessoas com deficiência que frequentam a escola, por idade",
        "IBGE, Censo Demográfico 2022: 2,4 milhões de pessoas com diagnóstico de autismo (1,2% da população)",
        "Lei nº 13.146/2015 (Lei Brasileira de Inclusão), art. 28, § 1º: escola particular não pode cobrar valor adicional pela inclusão; confirmado pelo STF na ADI 5357 (2016)",
        "Decreto nº 12.686/2025, alterado pelo Decreto nº 12.773/2025: Plano Educacional Individualizado (PEI) obrigatório",
        "Marques e Duarte (2013), citado no Manual PRISMA: a falta de tempo para planejar adaptações é a principal queixa dos professores",
    ]
    links = {  # endereços consultados em 31/10/2026
        "Notas Estatísticas do Censo Escolar 2025": "https://download.inep.gov.br/publicacoes/institucionais/estatisticas_e_indicadores/notas_estatisticas_censo_escolar_da_educacao_basica_2025.pdf",
        "Agência Gov": "https://agenciagov.ebc.com.br/noticias/202608/conheca-o-perfil-dos-46-milhoes-de-estudantes-da-educacao-basica-no-dia-do-estudante",
        "via Fenep": "https://www.fenep.org.br/rede-privada-consolida-recuperacao-apos-crise-sanitaria-e-ja-supera-95-milhoes-de-alunos/",
        "Saeb 2025": "https://todospelaeducacao.org.br/wordpress/wp-content/uploads/2026/08/estudo-evolucao-dos-niveis-de-aprendizagem-na-educacao-basica-2025-todos-pela-educacao.pdf",
        "Indicador Criança Alfabetizada": "https://agenciagov.ebc.com.br/noticias/202507/58-dos-municipios-melhoraram-alfabetizacao",
        "Portaria Interministerial nº 14/2025": "https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/financiamento/fundeb/Valoralunoanoereceitaanualprevista2026.pdf",
        "Gemini": "https://ai.google.dev/gemini-api/docs/pricing",
        "Melhor Escola": "https://www.melhorescola.com.br/artigos/quanto-custa-uma-escola-particular-no-ensino-fundamental",
        "Censo Demográfico 2022": "https://agenciadenoticias.ibge.gov.br/agencia-noticias/2012-agencia-de-noticias/noticias/43464",
        "Associação Brasileira de Dislexia": "https://www.bemparana.com.br/noticias/parana/dislexia-e-obstaculo-no-aprendizado-escolar/amp/",
    }

    def item(texto):
        url = next((u for chave, u in links.items() if chave in texto), None)
        return f'<li>{ESC(texto)}' + (f' <a href="{ESC(url)}">link</a>' if url else "") + "</li>"
    return "<ol>" + "".join(item(i) for i in itens) + "</ol>"


def logo_svg(largura="2.1in"):
    """Logo pixelada do PRISMA (web/assets/img/prisma-logo.svg), embutida no PDF."""
    svg = (RAIZ / "web" / "assets" / "img" / "prisma-logo.svg").read_text(encoding="utf-8")
    return svg.replace("<svg ", f'<svg class="logo" style="width:{largura};height:auto" role="img" aria-label="Logo do PRISMA" ', 1)


def imagem(caminho, alt, classe):
    b64 = base64.b64encode((RAIZ / caminho).read_bytes()).decode()
    return f'<img class="{classe}" src="data:image/png;base64,{b64}" alt="{ESC(alt)}">'


def slide(conteudo, classe=""):
    return (f'<section class="slide {classe}">{conteudo}'
            '<footer class="rodape-slide"><span>PRISMA · Plano de negócio · Time Carcará 3301 · Hackathon LEPV 2026</span>'
            '<span class="num"></span></footer></section>')


def cab(secao, titulo):
    return f'<p class="eyebrow">{ESC(secao)}</p><h2>{titulo}</h2>'


def documento():
    ma = DADOS_MANUAL
    reg = ma["registros_por_tipo_2024"]
    esc = ma["escolarizacao_por_idade_2022"]
    sa = ma["escolas_sem_acessibilidade_2024"]
    mt = ma["matriculas_total"]
    cc = ma["classes_comuns_4a17_2025"]
    form = ma["formacao"]
    e = EQ
    cen_p = CEN["pessimista"]
    receita = [l["receita"] for l in LIN]
    custo = [l["custo"] for l in LIN]
    caixa = [l["caixa"] for l in LIN]
    S = []

    # 1. capa: só apresentação
    S.append(f'''<section class="slide capa">
  <p class="eyebrow">Plano de negócio · Hackathon LEPV 2026 · Liga de Empreendedorismo da Praia Vermelha</p>
  <div class="capa-centro">
    {logo_svg()}
    <h1>PRISMA</h1>
    <p class="sigla">Plataforma de Recursos Inclusivos e Sala de Materiais Acessíveis</p>
  </div>
  <div class="capa-time">
    {imagem("web/assets/img/carcara.png", "Mascote do time: um carcará pixelado", "carcara")}
    <div><p class="time-nome">Time Carcará 3301</p>
    <p class="time-info">Instituto Militar de Engenharia (IME) · 31 de outubro de 2026</p></div>
  </div>
</section>''')

    # 2. os números que saíram da capa
    S.append(slide(f'''{cab("Em poucas palavras", "Uma aula entra. Várias versões saem. Todos aprendem juntos.")}
  <ul class="numeros">
    <li><b>{mi(P['ef'])}</b><span>alunos no ensino fundamental</span></li>
    <li><b>{mi(P['nucleo'])}</b><span>com uma necessidade específica (estimativa)</span></li>
    <li><b>R$ 60</b><span>por aluno por ano, menos de 1% de uma mensalidade</span></li>
    <li><b>{br(VAL['retorno'], 1)}×</b><span>o preço volta em horas de professor</span></li>
  </ul>
  <p class="nota-trilhas">Trilhas do hackathon: 1 (Inclusão e acessibilidade) e 4 (Aprendizagem individualizada).</p>'''))

    # 3 e 4. resumo
    S.append(slide(f'''{cab("Resumo", "Problema e tese")}
  <div class="duas">
  <div class="bloco"><h3>O problema</h3>
  <p>A escola brasileira já incluiu. As matrículas da educação especial passaram de {mi(mt['serie'][0]['valor'], 2)} em 2015 para {mi(mt['serie'][-1]['valor'])} em 2025, e {cc['comuns']}% desses alunos de 4 a 17 anos estudam em classes comuns. Mas incluir não é ensinar. Só {br(form['regentes_com_formacao_continuada_2024'], 1)}% dos professores regentes têm formação continuada na área. E metade dos alunos do fundamental termina o ano sem o aprendizado adequado em português.</p>
  <p>Para cada aluno com uma barreira, o professor adapta o material à mão. Isso leva horas que ele não tem. A falta de tempo é a principal queixa dos professores sobre inclusão.</p></div>
  <div class="bloco"><h3>A tese</h3>
  <p>O gargalo não é a vontade do professor. É o tempo. O PRISMA recebe o material da aula (PDF, slide, texto ou vídeo) e devolve, em segundos, versões acessíveis feitas com as regras do nosso Manual: letra ampliada e alto contraste, cor sempre com símbolo, passos numerados, texto mais direto e áudio.</p>
  <p>O professor revisa e aprova. O mesmo conteúdo chega a todos, cada um do seu jeito, sem laudo e sem rótulo.</p></div>
  </div>'''))
    S.append(slide(f'''{cab("Resumo", "Mercado e modelo")}
  <div class="duas">
  <div class="bloco"><h3>O mercado</h3>
  <p>São {mi(P['ef'])} de alunos no fundamental. Estimamos {mi(P['nucleo'])} com uma necessidade específica (deficiência, autismo, TDAH, dislexia ou daltonismo) e {mi(P['dificuldade'], 0)} com dificuldade de leitura.</p>
  <p>Começamos pelas {br(V['escolas_ef_privadas'])} escolas particulares com fundamental ({mi(P['privada'])} de alunos). Nelas, o diretor decide sem licitação, e a lei já obriga a escola a incluir sem cobrar a mais da família. Esse primeiro mercado vale {reais(R['sam'] / 1e6)} milhões por ano.</p></div>
  <div class="bloco"><h3>O modelo</h3>
  <p>A escola assina por tamanho: Essencial (até 200 alunos) {reais(PL['essencial']['anual'])} por ano, Escola (201 a 500) {reais(PL['escola']['anual'])} e Ampliado (501 a 1.000) {reais(PL['ampliado']['anual'])}. Há opção semestral e {M.TESTE_GRATIS_DIAS} dias de teste grátis. Isso dá cerca de R$ 60 por aluno por ano, e o valor volta {br(VAL['retorno'], 1)} vezes em horas de professor.</p>
  <p>Com {br(R['anos'][-1]['escolas_fim'])} escolas no fim de 2029 ({br(100 * R['som_parte'], 1)}% do mercado), chegamos a {reais(R['anos'][-1]['arr_fim'] / 1e6, 1)} milhões de receita anual recorrente. Buscamos {reais(APORTE)} de investidor-anjo para chegar ao lucro mensal em {mes_ano(e)}.</p></div>
  </div>'''))

    # 5 a 7. o problema em números
    S.append(slide(f'''{cab("1 · O problema em números", "A inclusão chegou à sala. O apoio ao professor, não.")}
  <div class="duas">
    {colunas("Matrículas da educação especial no Brasil", [(str(x['ano']), x['valor']) for x in mt['serie']], mt['fonte'], lambda v: mi(v, 2 if v < 1e6 else 1))}
    <div>{BM.medidor("Alunos da educação especial de 4 a 17 anos em classes comuns, 2025", cc['comuns'], "em classes comuns, com a turma", "em classes ou escolas exclusivas", cc['fonte'])}
    <div class="stat"><b>{br(form['regentes_com_formacao_continuada_2024'], 1)}%</b><span>dos professores regentes têm formação continuada na área (2024). Os outros {br(100 - form['regentes_com_formacao_continuada_2024'], 1)}% incluem sem preparo específico.</span><em>Fonte: {ESC(form['fonte'])}</em></div></div>
  </div>'''))
    S.append(slide(f'''{cab("1 · O problema em números", "Quem são os alunos da educação especial")}
  {BM.rosca(reg["fatias"], "Registros da educação especial por tipo, 2024 (gráfico do Manual PRISMA)", reg["fonte"], reg["nota"])}'''))
    S.append(slide(f'''{cab("1 · O problema em números", "O acesso foi conquistado. Falta aprender junto.")}
  <div class="duas">
    {BM.barras_h("Pessoas com deficiência que frequentam a escola, por idade (gráfico do Manual PRISMA)", [(f["faixa"], f["valor"]) for f in esc["faixas"]], esc["fonte"], esq=130, largura=520)}
    {BM.medidor("Escolas sem nenhum recurso de acessibilidade, 2024 (gráfico do Manual PRISMA)", sa["sem"], f"{br(sa['escolas_sem'])} escolas sem nenhum recurso", "escolas com pelo menos um recurso", sa["fonte"])}
  </div>
  <p class="destaque">Na faixa do ensino fundamental (6 a 14 anos), 95% das crianças com deficiência estão na escola. O que falta agora é aprender junto, e isso depende do material que chega às mãos do aluno.</p>'''))

    # 8 a 11. quem precisa
    S.append(slide(f'''{cab("2 · Quem precisa", "Muito além dos alunos com laudo")}
  <div class="lado">
    <div><p>O Censo Escolar conta só deficiência, autismo e altas habilidades.</p>
    <p><b>TDAH e dislexia não entram na conta da educação especial</b>, então esses alunos ficam sem apoio formal.</p>
    <p>O PRISMA não exige laudo: qualquer aluno que aprende melhor com letra maior, passos numerados ou texto mais direto usa as mesmas versões.</p></div>
    {BM.barras_h("Alunos do fundamental com cada necessidade (estimativa, em mil)", [("Educação especial", round(P['especial'] / 1e3)), ("TDAH", round(P['tdah'] / 1e3)), ("Dislexia", round(P['dislexia'] / 1e3)), ("Daltonismo", round(P['daltonismo'] / 1e3))], "cálculo do time (próximo slide)", maximo=2000, sufixo=" mil", esq=170)}
  </div>'''))
    S.append(slide(f'''{cab("2 · Quem precisa", "Como estimamos: 1 em cada 6 alunos")}
  <table class="t"><thead><tr><th>Grupo</th><th>Como estimamos</th><th>Alunos</th></tr></thead><tbody>
    <tr><td>Educação especial no fundamental</td><td>{mi(V['educ_especial_total'])} matrículas em 2025 × {br(100 * V['educ_especial_parte_ef'], 1)}% no fundamental</td><td class="num">{mi(P['especial'], 2)}</td></tr>
    <tr><td>TDAH</td><td>{br(100 * V['tdah'], 1)}% de {mi(P['ef'])} (estudo brasileiro com 1.830 crianças)</td><td class="num">{mi(P['tdah'], 2)}</td></tr>
    <tr><td>Dislexia</td><td>{br(100 * V['dislexia'])}%, o valor mais baixo da faixa de 5% a 17% da literatura</td><td class="num">{mi(P['dislexia'], 2)}</td></tr>
    <tr><td>Daltonismo</td><td>8% dos meninos e 0,5% das meninas</td><td class="num">{mi(P['daltonismo'], 2)}</td></tr>
    <tr><td><b>Total, sem contar a mesma criança duas vezes</b></td><td>Soma de {mi(P['soma'], 2)}, menos {br(100 * M.HIPOTESES['sobreposicao'])}% de sobreposição (por exemplo, TDAH e dislexia juntos)</td><td class="num"><b>{mi(P['nucleo'], 2)}</b></td></tr>
  </tbody></table>
  <p class="destaque">Cerca de <b>1 em cada 6 alunos</b> do fundamental ({br(100 * P['nucleo_pct'], 1)}%) tem uma necessidade específica. Numa turma de 30, são 5 alunos.</p>'''))
    S.append(slide(f'''{cab("2 · Quem precisa", "A dificuldade de leitura é da metade da turma")}
  <div class="lado inverso">
    {barras_duplas("Alunos SEM aprendizado adequado, Saeb 2025", [("5º ano", [100 * (1 - V['saeb_5_lp']), 100 * (1 - V['saeb_5_mt'])]), ("9º ano", [100 * (1 - V['saeb_9_lp']), 100 * (1 - V['saeb_9_mt'])])], [("Língua Portuguesa", AZUL), ("Matemática", LARANJA)], "Saeb 2025, análise do Todos Pela Educação (agosto de 2026)", altura=230)}
    <div><p>Além disso, {br(100 * (1 - V['alfabetizadas_2ano']), 1)}% das crianças da rede pública não estavam alfabetizadas no fim do 2º ano em 2024.</p>
    <p>Essas crianças não têm diagnóstico, mas enfrentam a mesma barreira: um texto longo e denso.</p>
    <p>As versões de Leitura Fácil, áudio e passos numerados ajudam todas elas.</p></div>
  </div>'''))
    S.append(slide(f'''{cab("2 · Quem precisa", "Do total da turma ao primeiro mercado")}
  <div class="funil">{figura_funil()}</div>
  <p class="destaque">Por isso defendemos o preço por escola, e não por aluno com laudo: <b>a escola paga uma vez e a turma inteira usa</b>.</p>'''))

    # 12 e 13. mercado
    S.append(slide(f'''{cab("3 · Mercado", "Começar pela escola particular, crescer para as redes públicas")}
  <ul class="cartoes">
    <li><em>Mercado total</em><b>{reais(R['tam'] / 1e9, 2)} bilhão</b><span>por ano: todos os {mi(P['ef'])} de alunos do fundamental a R$ 60</span></li>
    <li><em>Primeiro mercado</em><b>{reais(R['sam'] / 1e6)} milhões</b><span>por ano: as {br(V['escolas_ef_privadas'])} escolas particulares com fundamental ({mi(P['privada'])} de alunos)</span></li>
    <li><em>Meta em 3 anos</em><b>{br(R['anos'][-1]['escolas_fim'])} escolas</b><span>em dez/2029, só {br(100 * R['som_parte'], 1)}% das particulares, com {reais(R['anos'][-1]['arr_fim'] / 1e6, 1)} milhões por ano</span></li>
  </ul>
  <h3>Depois, as redes públicas</h3>
  <p>A partir de 2029, com casos de uso nas escolas particulares, vendemos para prefeituras. R$ 60 por aluno por ano é {br(100 * R['fundeb_parte'], 1)}% do valor mínimo que o Fundeb garante por aluno ({reais(V['fundeb_vaaf_min'], 2)} em 2026). Um plano para famílias, para a lição de casa, fica para uma fase seguinte.</p>'''))
    S.append(slide(f'''{cab("3 · Mercado", "Por que a escola particular primeiro")}
  <ul class="lista grande">
    <li><b>Decisão rápida.</b> O diretor ou o mantenedor assina, sem licitação. Na rede pública, o ciclo leva de 6 a 12 meses.</li>
    <li><b>Obrigação legal sem verba extra.</b> A Lei Brasileira de Inclusão proíbe cobrar a mais da família pela inclusão, e o STF confirmou isso em 2016. O custo de adaptar fica com a escola. O PRISMA reduz esse custo.</li>
    <li><b>Documento obrigatório.</b> O Plano Educacional Individualizado (PEI) passou a ser obrigatório em 2025. O PRISMA registra cada adaptação feita, o que ajuda a montar o PEI.</li>
    <li><b>Tamanho certo.</b> A escola particular média com fundamental tem {br(P['alunos_por_escola_privada'])} alunos. Ela cabe no plano Essencial, o de entrada.</li>
  </ul>'''))

    # 14 a 16. modelo e preço
    S.append(slide(f'''{cab("4 · Modelo e preço", "Três planos, por tamanho da escola")}
  {tabela_planos()}
  <p class="nota">Âncora de R$ 60 por aluno por ano, no meio de cada faixa. Quanto mais a escola cresce dentro da faixa, menor o preço por aluno.</p>'''))
    S.append(slide(f'''{cab("4 · Modelo e preço", "Como cobramos")}
  <ul class="lista grande">
    <li><b>A escola pequena paga mais por aluno.</b> Com 100 alunos, o Essencial sai a R$ 90 por aluno por ano. Ainda assim, são R$ 7,50 por mês, menos de 2% de uma mensalidade de R$ 500.</li>
    <li><b>Semestral custa 10% a mais</b> que metade do anual. A escola testa por um semestre, e o anual fica mais vantajoso na renovação.</li>
    <li><b>{M.TESTE_GRATIS_DIAS} dias de teste grátis</b>, sem cartão e com implantação acompanhada. São duas semanas de aula: o professor adapta, usa em sala e vê a reação dos alunos, e a coordenação decide na reunião semanal.</li>
    <li><b>O teste custa quase nada para nós:</b> cerca de {reais(R['ia_material'], 2)} de IA por material adaptado.</li>
  </ul>'''))
    S.append(slide(f'''{cab("4 · Modelo e preço", f"Por que a escola paga: o preço volta {br(VAL['retorno'], 1)} vezes")}
  <div class="lado">
  <table class="t"><tbody>
    <tr><td>Professores do fundamental numa escola de 200 alunos</td><td class="num">{M.HIPOTESES['professores_por_200']}</td></tr>
    <tr><td>Horas por semana que cada um gasta adaptando material sozinho (hipótese a medir no piloto)</td><td class="num">{br(M.HIPOTESES['horas_por_professor'])} h</td></tr>
    <tr><td>Horas economizadas por mês</td><td class="num">{br(VAL['horas_mes'])} h</td></tr>
    <tr><td>Valor da hora pelo piso nacional de 2026 ({reais(V['piso_professor'], 2)} por 40 horas semanais)</td><td class="num">{reais(VAL['hora'], 2)}</td></tr>
    <tr><td><b>Valor das horas economizadas por mês</b></td><td class="num"><b>{reais(VAL['economia_mes'])}</b></td></tr>
    <tr><td><b>Preço do plano Essencial por mês</b></td><td class="num"><b>{reais(VAL['preco_mes'])}</b></td></tr>
  </tbody></table>
  <p class="destaque">Para uma família que paga de R$ 500 a R$ 2.000 de mensalidade, o PRISMA custa à escola de R$ 3,75 a R$ 5 por aluno por mês: <b>menos de 1% da mensalidade</b>. Usamos o piso salarial, o valor mais baixo possível. Com o salário real da escola particular, o retorno é maior.</p>
  </div>'''))

    # 17. custos
    S.append(slide(f'''{cab("5 · Quanto custa entregar", "Custo baixo por escola, margem alta")}
  <table class="t compacta"><thead><tr><th>Item</th><th>Valor</th><th>Como calculamos</th></tr></thead><tbody>
    <tr><td>IA por material adaptado</td><td class="num">{reais(R['ia_material'], 2)}</td><td>Duas páginas, dois níveis de Leitura Fácil, duas imagens descritas e 20% de reenvio, no preço da API Gemini 3.1 Flash-Lite, com dólar a R$ {br(M.HIPOTESES['dolar'], 2)}</td></tr>
    <tr><td>Servidor, IA e suporte por escola ativa</td><td class="num">{reais(M.HIPOTESES['custo_var_escola_mes'])}/mês</td><td>Cobre cerca de 1.000 materiais por mês, muito acima do uso esperado</td></tr>
    <tr><td>Receita média por escola</td><td class="num">{reais(R['ticket_mes'])}/mês</td><td>55% no Essencial, 35% no Escola e 10% no Ampliado, com 40% no semestral</td></tr>
    <tr><td>Impostos e taxas de pagamento</td><td class="num">8% a 13,5%</td><td>Simples Nacional, Anexo III (alíquota efetiva crescente), mais 2% de boleto, PIX e cartão</td></tr>
    <tr><td><b>O que sobra por escola, por mês</b></td><td class="num"><b>{reais(R['margem_contrib_mes'])}</b></td><td>Receita menos impostos, taxas e custo por escola</td></tr>
    <tr><td>Custo para conquistar uma escola</td><td class="num">{reais(M.HIPOTESES['cac'])}</td><td>Comissão de venda, eventos de educação, visita, demonstração e acompanhamento do teste</td></tr>
    <tr><td><b>Esse custo se paga em</b></td><td class="num"><b>{br(R['payback_meses'], 1)} meses</b></td><td>Custo para conquistar ÷ o que sobra por mês</td></tr>
    <tr><td><b>Cada escola rende, em 3 anos</b></td><td class="num"><b>{br(R['ltv_cac'], 1)}×</b></td><td>o que custou para conquistá-la ({reais(R['ltv_36'])} contra {reais(M.HIPOTESES['cac'])})</td></tr>
  </tbody></table>
  <p class="destaque">O custo da IA é tão baixo que <b>não é ele que decide o preço</b>. O preço vem do valor para a escola (as horas de professor).</p>'''))

    # 18 e 19. projeção
    S.append(slide(f'''{cab("6 · Projeção de 3 anos (cenário base)", f"Lucro todo mês a partir de {mes_ano(e)}")}
  <p>Lançamos em fevereiro de 2027, no começo do ano letivo. As vendas se concentram em fevereiro e março e em julho e agosto, quando as escolas planejam o semestre. Metas de novas escolas: {', '.join(br(x) for x in M.NOVAS_POR_ANO)} em 2027, 2028 e 2029. Supomos que 20% das escolas cancelam por ano.</p>
  {tabela_anos()}
  <p>A equipe cresce em degraus: 4 fundadores com ajuda de custo nos primeiros meses, 2 contratações em 2028 (vendas e suporte) e 6 em 2029. Por isso os custos sobem em janeiro de cada ano, e a receita alcança depois.</p>'''))
    S.append(slide(f'''{cab("6 · Projeção de 3 anos (cenário base)", "Receita e custos, mês a mês")}
  {linhas("Receita e custos por mês", [("Receita", AZUL, receita), ("Custos", LARANJA, custo)], "modelo do time (modelo.py)", marcar=(e['m'] - 1, f"lucro a partir de {mes_ano(e)}") if e else None, altura=250)}'''))

    # 20 a 23. investimento e cenários
    S.append(slide(f'''{cab("7 · Investimento", f"{reais(APORTE)} de investidor-anjo")}
  <div class="lado inverso">
    {linhas("Dinheiro acumulado em caixa, mês a mês (cenário base, sem o investimento)", [("Caixa", AZUL, caixa)], "modelo do time (modelo.py)", zero=True, marcar=(R['pior_mes']['m'] - 1, f"pior momento: {reais(R['pior_mes']['caixa'])}"), altura=290)}
    <div><p>No cenário base, o caixa chega ao ponto mais baixo em {mes_ano(R['pior_mes'])}, com {reais(R['investimento'])} negativos.</p>
    <p>Pedimos <b>{reais(APORTE)}</b>: cobre esse valor com cerca de {br(100 * (APORTE / R['investimento'] - 1))}% de folga para atrasos de venda.</p>
    <p>A participação societária será negociada com o investidor. Nossa proposta de partida é 12,5%.</p></div>
  </div>'''))
    S.append(slide(f'''{cab("7 · Investimento", "Para onde vai o dinheiro")}
  <div class="lado inverso">
    {uso_recursos()}
    <div><p>Mais da metade do dinheiro vai para conquistar escolas: vendedor, eventos de educação, visitas e o acompanhamento do teste grátis.</p>
    <p class="destaque">O produto já existe e funciona. O que falta é chegar às escolas.</p></div>
  </div>'''))
    S.append(slide(f'''{cab("7 · Investimento", "E se as vendas forem piores?")}
  {tabela_cenarios()}
  <p class="destaque">No cenário pessimista, o negócio ainda chega a {br(cen_p['escolas_fim'])} escolas e lucro mensal{(' em ' + mes_ano(cen_p['equilibrio'])) if cen_p['equilibrio'] else ''}, mas precisaria de {reais(cen_p['investimento'])}. Regra de segurança: se as vendas do 1º semestre de 2027 ficarem abaixo do pessimista, adiamos as contratações de 2028 antes de usar mais dinheiro.</p>'''))
    S.append(slide(f'''{cab("7 · Investimento", "Marcos que o investidor pode cobrar")}
  {tabela_marcos()}'''))

    # 24 e 25. riscos e próximos passos
    S.append(slide(f'''{cab("8 · Riscos", "O que pode dar errado e como reduzimos")}
  <table class="t compacta"><thead><tr><th>Risco</th><th>Como reduzimos</th></tr></thead><tbody>
    <tr><td>A escola não ver valor no teste</td><td>{M.TESTE_GRATIS_DIAS} dias de teste com implantação acompanhada e um relatório de horas economizadas no fim do teste.</td></tr>
    <tr><td>A IA errar</td><td>Nada chega ao aluno sem o professor aprovar. Regras automáticas conferem o texto da IA (frases curtas, sem abreviações) e devolvem para correção.</td></tr>
    <tr><td>O preço da IA subir ou o fornecedor mudar</td><td>Trocar de fornecedor é mudar uma função no código. O custo atual por material é cerca de {reais(R['ia_material'], 2)}: uma alta de 10 vezes ainda caberia no preço.</td></tr>
    <tr><td>Dados de crianças (LGPD)</td><td>Só registramos necessidades de aprendizagem, nunca diagnóstico. Alunos entram com apelido e figurinhas. No plano pago da IA, os dados não treinam o modelo.</td></tr>
    <tr><td>Vendas sazonais</td><td>Vendas concentradas no início de cada semestre, plano semestral para quem quer testar e caixa para os meses de baixa.</td></tr>
    <tr><td>Um concorrente grande copiar</td><td>Nosso diferencial é o Manual: 51 critérios com evidências, que viram regras no código. Some-se o foco no tempo do professor e o preço de entrada baixo.</td></tr>
  </tbody></table>'''))
    S.append(slide(f'''{cab("9 · Próximos passos", "O que fazemos com o investimento")}
  <ol class="lista grande passos">
    <li><b>Piloto gratuito em 3 escolas particulares</b> no 1º semestre de 2027, medindo as horas economizadas.</li>
    <li><b>Validar com professores e com o AEE</b> os parâmetros do Manual marcados como "a testar".</li>
    <li><b>Rodada anjo de {reais(APORTE)}</b> para contratar vendas e suporte em 2028.</li>
  </ol>
  <div class="fim-time">{imagem("web/assets/img/carcara.png", "Mascote do time: um carcará pixelado", "carcara pequeno")}<p><b>Time Carcará 3301</b> · obrigado!</p></div>'''))

    # 26 e 27. fontes e hipóteses
    S.append(slide(f'''{cab("Fontes", "De onde vêm os números")}
  <div class="fontes">{fontes_lista()}</div>'''))
    S.append(slide(f'''{cab("Hipóteses", "O que ainda vamos validar no piloto")}
  <ul class="lista grande">
    <li>Sobreposição de {br(100 * M.HIPOTESES['sobreposicao'])}% entre as necessidades.</li>
    <li>{M.HIPOTESES['professores_por_200']} professores por escola de 200 alunos.</li>
    <li>{br(M.HIPOTESES['horas_por_professor'])} horas por semana de adaptação manual por professor.</li>
    <li>20% das escolas cancelam por ano.</li>
    <li>Custo de {reais(M.HIPOTESES['cac'])} para conquistar uma escola.</li>
    <li>Dólar a R$ {br(M.HIPOTESES['dolar'], 2)}. Alíquota efetiva do Simples Nacional de 6% a 11,5%.</li>
  </ul>'''))

    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>PRISMA · Plano de negócio</title>
<style>{fontes()}{CSS}</style></head><body>{"".join(S)}</body></html>"""


CSS = """
@page { size: 13.333in 7.5in; margin: 0; }
:root { --ink:#1E2235; --muted:#4A4F6A; --line:#D9D3C4; --soft:#F3EDDF; --blue:#1F6FB2; --laranja:#A3401F; --papel:#FBF7EE;
  --display:'Pixelify Sans','Atkinson Hyperlegible Next',system-ui,sans-serif; --body:'Atkinson Hyperlegible Next',system-ui,sans-serif; --mono:'Departure Mono',ui-monospace,monospace; }
* { box-sizing:border-box; }
html, body { margin:0; }
body { color:var(--ink); background:#fff; font:15pt/1.45 var(--body); counter-reset: slide; }
.slide { position:relative; width:13.333in; height:7.5in; padding:.5in .7in .75in; overflow:hidden; break-after:page; counter-increment: slide; }
.slide:last-child { break-after:auto; }
h1,h2,h3 { font-family:var(--display); font-weight:400; line-height:1.15; margin:0 0 10pt; }
h2 { font-size:27pt; margin-bottom:16pt; }
h3 { font-size:17pt; margin:6pt 0 8pt; }
p { margin:0 0 9pt; }
.eyebrow { font-family:var(--mono); font-size:11pt; letter-spacing:.05em; color:var(--blue); margin:0 0 6pt; }
.rodape-slide { position:absolute; left:.7in; right:.7in; bottom:.3in; display:flex; justify-content:space-between; font-size:9.5pt; color:var(--muted); border-top:1px solid var(--line); padding-top:5pt; }
.rodape-slide .num::before { content: counter(slide); }
.mono { font-family:var(--mono); font-size:.92em; }

/* capa */
.capa { background:var(--papel); border:6px solid var(--ink); display:flex; flex-direction:column; padding:.55in .8in; }
.capa .eyebrow { font-size:12pt; }
.capa-centro { flex:1; display:flex; flex-direction:column; justify-content:center; align-items:flex-start; }
.capa .logo { display:block; margin-bottom:14pt; }
.capa h1 { font-size:84pt; font-weight:700; margin:0; letter-spacing:.02em; }
.capa .sigla { font-size:19pt; color:var(--muted); margin-top:6pt; }
.capa-time { display:flex; align-items:center; gap:18pt; border-top:3px solid var(--ink); padding-top:16pt; }
.carcara { height:1.05in; width:auto; image-rendering:pixelated; }
.time-nome { font-family:var(--display); font-size:30pt; margin:0; line-height:1.1; }
.time-info { margin:4pt 0 0; color:var(--muted); font-size:13pt; }

/* blocos */
.duas { display:grid; grid-template-columns:1fr 1fr; gap:26pt; align-items:start; }
.lado { display:grid; grid-template-columns:1.25fr 1fr; gap:26pt; align-items:center; }
.lado.inverso { grid-template-columns:1.35fr 1fr; }
.bloco { border-left:5pt solid var(--blue); padding:2pt 0 2pt 14pt; }
.bloco h3 { margin-top:0; }
.bloco p { font-size:14pt; }
.numeros { list-style:none; padding:0; margin:34pt 0 26pt; display:grid; grid-template-columns:repeat(4,1fr); gap:18pt; }
.numeros li { border:3px solid var(--ink); background:var(--papel); padding:24pt 18pt; display:grid; gap:12pt; align-content:start; min-height:3.1in; }
.numeros b { font-size:40pt; line-height:1; white-space:nowrap; }
.numeros span { color:var(--muted); font-size:16pt; }
.stat { border:3px solid var(--ink); background:var(--papel); padding:14pt 16pt; display:grid; gap:6pt; }
.stat b { font-size:40pt; line-height:1; }
.stat span { font-size:14pt; }
.stat em { font-style:normal; font-size:10pt; color:var(--muted); }
.nota-trilhas, .nota { color:var(--muted); font-size:13pt; }

/* gráficos */
figure { margin:0 0 12pt; }
.grafico { width:100%; height:auto; max-height:4.1in; font-family:var(--body); }
.duas .grafico, .lado .grafico { max-height:3.7in; }
figcaption.tit { font-family:var(--display); font-weight:400; font-size:14pt; margin-bottom:8pt; }
figcaption.fonte { font-size:10pt; color:var(--muted); margin-top:5pt; }
.rosca-grade { display:grid; grid-template-columns:3.6in 1fr; gap:28pt; align-items:center; }
.leg-rosca { list-style:none; padding:0; margin:0; font-size:14pt; }
.leg-rosca li { display:grid; grid-template-columns:16pt 1fr auto 1.4in; gap:10pt; align-items:baseline; padding:6pt 0; border-top:1px solid var(--line); }
.leg-rosca i { width:13pt; height:13pt; display:inline-block; transform:translateY(1pt); outline:1.5pt solid var(--ink); }
.leg-rosca b { font-variant-numeric:tabular-nums; }
.leg-rosca em { font-style:normal; color:var(--muted); text-align:right; font-variant-numeric:tabular-nums; }
.medidor { margin-bottom:22pt; }
.medidor .trilho { height:34pt; background:var(--soft); border:1px solid var(--line); overflow:hidden; }
.medidor .trilho span { display:flex; align-items:center; justify-content:flex-end; height:100%; background:var(--ink); color:#fff; padding-right:8pt; font-size:14pt; }
.med-leg { display:flex; flex-wrap:wrap; gap:4pt 18pt; font-size:12pt; margin-top:6pt; }
.legenda { list-style:none; padding:0; margin:0 0 6pt; display:flex; gap:20pt; font-size:13pt; }
.legenda i { display:inline-block; width:13pt; height:13pt; margin-right:6pt; outline:1.5pt solid var(--ink); transform:translateY(1pt); }

/* tabelas e listas */
.t { width:100%; border-collapse:collapse; font-size:13pt; margin:4pt 0 14pt; }
.t.compacta { font-size:11pt; }
.funil .grafico { max-height:3.3in; }
.t th { text-align:left; font-weight:700; border-bottom:2px solid var(--ink); padding:6pt 8pt; vertical-align:bottom; }
.t td { border-bottom:1px solid var(--line); padding:6pt 8pt; vertical-align:top; }
.t.compacta td, .t.compacta th { padding:4.5pt 8pt; }
.t .num { text-align:right; white-space:nowrap; font-variant-numeric:tabular-nums; }
.t .neg { color:var(--laranja); }
.t .sub { display:block; color:var(--muted); font-size:.82em; }
.destaque { background:var(--soft); border:2px solid var(--ink); padding:10pt 14pt; }
.cartoes { list-style:none; padding:0; margin:0 0 18pt; display:grid; grid-template-columns:repeat(3,1fr); gap:16pt; }
.cartoes li { border:3px solid var(--ink); padding:14pt; display:grid; gap:6pt; align-content:start; }
.cartoes b { font-size:24pt; }
.cartoes span { font-size:13pt; color:var(--muted); }
.cartoes em { font-style:normal; font-family:var(--mono); font-size:11pt; color:var(--blue); }
.lista { padding-left:20pt; }
.lista li { margin-bottom:7pt; }
.lista.grande li { font-size:16pt; margin-bottom:14pt; }
.passos li { margin-bottom:18pt; }
.fim-time { position:absolute; right:.7in; bottom:.85in; display:flex; align-items:center; gap:12pt; font-family:var(--display); font-size:18pt; }
.carcara.pequeno { height:.8in; }
.fontes ol { font-size:10.5pt; padding-left:20pt; columns:2; column-gap:28pt; margin:0; }
.fontes li { margin-bottom:4pt; break-inside:avoid; }
.fontes a { color:var(--blue); }
"""


def main():
    destino = AQUI / "plano-de-negocio-prisma.pdf"
    pagina = AQUI / "plano-de-negocio-prisma.html"
    pagina.write_text(documento(), encoding="utf-8")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        nav = pw.chromium.launch(channel=CANAL) if CANAL else pw.chromium.launch()
        pg = nav.new_page()
        pg.goto(pagina.resolve().as_uri())
        pg.wait_for_timeout(600)
        # slides 16:9; o rodapé (nome e número) está em cada slide
        pg.pdf(path=str(destino), width="13.333in", height="7.5in", print_background=True, prefer_css_page_size=True)
        nav.close()
    print("ok:", destino)


if __name__ == "__main__":
    main()
