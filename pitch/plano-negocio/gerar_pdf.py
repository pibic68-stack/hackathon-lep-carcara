"""Gera o Plano de Negócio do PRISMA em PDF a partir do modelo (modelo.py) e dos dados do manual.

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
            'estimativa do time para necessidades específicas (página 4). As faixas se sobrepõem: cada uma está contida na anterior, '
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
            "base": "as hipóteses da página 9", "otimista": "40% mais vendas, 30% menos cancelamentos e aquisição 20% mais barata"}
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

    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>PRISMA · Plano de negócio</title>
<style>{fontes()}{CSS}</style></head><body>

<section class="capa">
  <p class="eyebrow">Plano de negócio · Hackathon LEP 2026 · Trilhas 1 e 4</p>
  <h1>PRISMA</h1>
  <p class="sigla">Plataforma de Recursos Inclusivos e Sala de Materiais Acessíveis</p>
  <p class="lema">Uma aula entra. Várias versões saem. Todos aprendem juntos.</p>
  <ul class="capa-numeros">
    <li><b>{mi(P['ef'])}</b><span>alunos no ensino fundamental</span></li>
    <li><b>{mi(P['nucleo'])}</b><span>com uma necessidade específica (estimativa)</span></li>
    <li><b>R$ 60</b><span>por aluno por ano, menos de 1% de uma mensalidade</span></li>
    <li><b>{br(VAL['retorno'], 1)}×</b><span>o preço volta em horas de professor</span></li>
  </ul>
  <p class="time">Time Carcará 3301 · Instituto Militar de Engenharia (IME) · 31 de outubro de 2026</p>
</section>

<section class="pagina">
  <p class="eyebrow">Resumo</p>
  <h2>Problema e tese, mercado e modelo</h2>
  <div class="bloco"><h3>O problema</h3>
  <p>A escola brasileira já incluiu. As matrículas da educação especial passaram de {mi(mt['serie'][0]['valor'], 2)} em 2015 para {mi(mt['serie'][-1]['valor'])} em 2025, e {cc['comuns']}% desses alunos de 4 a 17 anos estudam em classes comuns. Mas incluir não é ensinar. Só {br(form['regentes_com_formacao_continuada_2024'], 1)}% dos professores regentes têm formação continuada em educação especial. E metade dos alunos do fundamental termina o ano sem o aprendizado adequado em português.</p>
  <p>Para cada aluno com uma barreira, o professor precisa adaptar o material à mão: aumentar a letra, trocar a cor por símbolo, dividir a instrução em passos, simplificar o texto. Isso leva horas que ele não tem. A falta de tempo é a principal queixa dos professores sobre inclusão.</p></div>
  <div class="bloco"><h3>A tese</h3>
  <p>O gargalo não é a vontade do professor. É o tempo. O PRISMA recebe o material da aula (PDF, slide, texto ou vídeo) e devolve, em segundos, versões acessíveis feitas com as regras do nosso Manual: letra ampliada e alto contraste, cor sempre com símbolo, passos numerados, texto mais direto e áudio. O professor revisa e aprova. O mesmo conteúdo chega a todos, cada um do seu jeito, sem laudo e sem rótulo.</p></div>
  <div class="bloco"><h3>O mercado</h3>
  <p>São {mi(P['ef'])} de alunos no fundamental. Estimamos {mi(P['nucleo'])} com uma necessidade específica (deficiência, autismo, TDAH, dislexia ou daltonismo) e {mi(P['dificuldade'], 0)} com dificuldade de leitura. Começamos pelas {br(V['escolas_ef_privadas'])} escolas particulares com fundamental ({mi(P['privada'])} de alunos). Nelas, o diretor decide sem licitação, e a lei já obriga a escola a incluir sem cobrar a mais da família. Esse primeiro mercado vale {reais(R['sam'] / 1e6)} milhões por ano.</p></div>
  <div class="bloco"><h3>O modelo</h3>
  <p>A escola assina por tamanho. O Essencial, até 200 alunos, custa {reais(PL['essencial']['anual'])} por ano. O Escola, de 201 a 500, custa {reais(PL['escola']['anual'])}. O Ampliado, de 501 a 1.000, custa {reais(PL['ampliado']['anual'])}. Há opção semestral e {M.TESTE_GRATIS_DIAS} dias de teste grátis. Isso dá cerca de R$ 60 por aluno por ano, e o valor volta {br(VAL['retorno'], 1)} vezes em horas de professor. Com {br(R['anos'][-1]['escolas_fim'])} escolas no fim de 2029 ({br(100 * R['som_parte'], 1)}% do mercado), chegamos a {reais(R['anos'][-1]['arr_fim'] / 1e6, 1)} milhões de receita anual recorrente. Buscamos {reais(APORTE)} de investidor-anjo para chegar ao lucro mensal em {mes_ano(e)}.</p></div>
</section>

<section class="pagina">
  <p class="eyebrow">1 · O problema em números</p>
  <h2>A inclusão chegou à sala. O apoio ao professor, não.</h2>
  <div class="duas">
    {colunas("Matrículas da educação especial no Brasil", [(str(x['ano']), x['valor']) for x in mt['serie']], mt['fonte'], lambda v: mi(v, 2 if v < 1e6 else 1))}
    {BM.medidor(f"Alunos da educação especial de 4 a 17 anos em classes comuns, 2025", cc['comuns'], "em classes comuns, com a turma", "em classes ou escolas exclusivas", cc['fonte'])}
  </div>
  {BM.rosca(reg["fatias"], "Registros da educação especial por tipo, 2024 (gráfico do Manual PRISMA)", reg["fonte"], reg["nota"])}
  <div class="duas">
    {BM.barras_h("Pessoas com deficiência que frequentam a escola, por idade (gráfico do Manual PRISMA)", [(f["faixa"], f["valor"]) for f in esc["faixas"]], esc["fonte"], esq=130, largura=520)}
    {BM.medidor("Escolas sem nenhum recurso de acessibilidade, 2024 (gráfico do Manual PRISMA)", sa["sem"], f"{br(sa['escolas_sem'])} escolas sem nenhum recurso", "escolas com pelo menos um recurso", sa["fonte"])}
  </div>
  <p class="destaque">Na faixa do ensino fundamental (6 a 14 anos), 95% das crianças com deficiência estão na escola. O acesso foi conquistado. O que falta agora é aprender junto, e isso depende do material que chega às mãos do aluno.</p>
</section>

<section class="pagina">
  <p class="eyebrow">2 · Quem precisa</p>
  <h2>Muito além dos alunos com laudo</h2>
  <p>O Censo Escolar conta só deficiência, autismo e altas habilidades. <b>TDAH e dislexia não entram na conta da educação especial</b>, então esses alunos ficam sem apoio formal. E o PRISMA não exige laudo: qualquer aluno que aprende melhor com letra maior, passos numerados ou texto mais direto usa as mesmas versões.</p>
  {BM.barras_h("Alunos do fundamental com cada necessidade (estimativa, em mil)", [("Educação especial", round(P['especial'] / 1e3)), ("TDAH", round(P['tdah'] / 1e3)), ("Dislexia", round(P['dislexia'] / 1e3)), ("Daltonismo", round(P['daltonismo'] / 1e3))], "cálculo do time sobre os dados da tabela abaixo", maximo=2000, sufixo=" mil", esq=170)}
  <table class="t"><thead><tr><th>Grupo</th><th>Como estimamos</th><th>Alunos</th></tr></thead><tbody>
    <tr><td>Educação especial no fundamental</td><td>{mi(V['educ_especial_total'])} matrículas em 2025 × {br(100 * V['educ_especial_parte_ef'], 1)}% no fundamental</td><td class="num">{mi(P['especial'], 2)}</td></tr>
    <tr><td>TDAH</td><td>{br(100 * V['tdah'], 1)}% de {mi(P['ef'])} (estudo brasileiro com 1.830 crianças)</td><td class="num">{mi(P['tdah'], 2)}</td></tr>
    <tr><td>Dislexia</td><td>{br(100 * V['dislexia'])}%, o valor mais baixo da faixa de 5% a 17% da literatura</td><td class="num">{mi(P['dislexia'], 2)}</td></tr>
    <tr><td>Daltonismo</td><td>8% dos meninos e 0,5% das meninas</td><td class="num">{mi(P['daltonismo'], 2)}</td></tr>
    <tr><td><b>Total, sem contar a mesma criança duas vezes</b></td><td>Soma de {mi(P['soma'], 2)}, menos {br(100 * M.HIPOTESES['sobreposicao'])}% de sobreposição (por exemplo, TDAH e dislexia juntos)</td><td class="num"><b>{mi(P['nucleo'], 2)}</b></td></tr>
  </tbody></table>
  <p class="destaque">Cerca de <b>1 em cada 6 alunos</b> do fundamental ({br(100 * P['nucleo_pct'], 1)}%) tem uma necessidade específica. Numa turma de 30, são 5 alunos.</p>
</section>

<section class="pagina">
  <p class="eyebrow">2 · Quem precisa (continuação)</p>
  <h2>A dificuldade de leitura é da metade da turma</h2>
  {barras_duplas("Alunos SEM aprendizado adequado, Saeb 2025", [("5º ano", [100 * (1 - V['saeb_5_lp']), 100 * (1 - V['saeb_5_mt'])]), ("9º ano", [100 * (1 - V['saeb_9_lp']), 100 * (1 - V['saeb_9_mt'])])], [("Língua Portuguesa", AZUL), ("Matemática", LARANJA)], "Saeb 2025, análise do Todos Pela Educação (agosto de 2026)", altura=210)}
  <p>Além disso, {br(100 * (1 - V['alfabetizadas_2ano']), 1)}% das crianças da rede pública não estavam alfabetizadas no fim do 2º ano em 2024. Essas crianças não têm diagnóstico, mas enfrentam a mesma barreira: um texto longo e denso. As versões de Leitura Fácil, áudio e passos numerados ajudam todas elas.</p>
  {figura_funil()}
  <p class="destaque">Por isso defendemos o preço por escola, e não por aluno com laudo: <b>a escola paga uma vez e a turma inteira usa</b>.</p>
</section>

<section class="pagina">
  <p class="eyebrow">3 · Mercado</p>
  <h2>Começar pela escola particular, crescer para as redes públicas</h2>
  <ul class="cartoes">
    <li><b>{reais(R['tam'] / 1e9, 2)} bilhão</b><span>por ano: todos os {mi(P['ef'])} de alunos do fundamental a R$ 60</span><em>Mercado total</em></li>
    <li><b>{reais(R['sam'] / 1e6)} milhões</b><span>por ano: as {br(V['escolas_ef_privadas'])} escolas particulares com fundamental ({mi(P['privada'])} de alunos)</span><em>Primeiro mercado</em></li>
    <li><b>{br(R['anos'][-1]['escolas_fim'])} escolas</b><span>em dez/2029, só {br(100 * R['som_parte'], 1)}% das particulares, com {reais(R['anos'][-1]['arr_fim'] / 1e6, 1)} milhões por ano</span><em>Meta em 3 anos</em></li>
  </ul>
  <h3>Por que a escola particular primeiro</h3>
  <ul class="lista">
    <li><b>Decisão rápida.</b> O diretor ou o mantenedor assina, sem licitação. Na rede pública, o ciclo leva de 6 a 12 meses.</li>
    <li><b>Obrigação legal sem verba extra.</b> A Lei Brasileira de Inclusão proíbe cobrar a mais da família pela inclusão, e o STF confirmou isso em 2016. O custo de adaptar fica com a escola. O PRISMA reduz esse custo.</li>
    <li><b>Documento obrigatório.</b> O Plano Educacional Individualizado (PEI) passou a ser obrigatório em 2025. O PRISMA registra cada adaptação feita, o que ajuda a montar o PEI.</li>
    <li><b>Tamanho certo.</b> A escola particular média com fundamental tem {br(P['alunos_por_escola_privada'])} alunos. Ela cabe no plano Essencial, o de entrada.</li>
  </ul>
  <h3>Depois, as redes públicas</h3>
  <p>A partir de 2029, com casos de uso nas escolas particulares, vendemos para prefeituras. R$ 60 por aluno por ano é {br(100 * R['fundeb_parte'], 1)}% do valor mínimo que o Fundeb garante por aluno ({reais(V['fundeb_vaaf_min'], 2)} em 2026). Um plano para famílias, para usar na lição de casa, fica para uma fase seguinte.</p>
</section>

<section class="pagina">
  <p class="eyebrow">4 · Modelo e preço</p>
  <h2>Três planos, por tamanho da escola</h2>
  {tabela_planos()}
  <ul class="lista">
    <li><b>Âncora de R$ 60 por aluno por ano</b>, no meio de cada faixa. Quanto mais a escola cresce dentro da faixa, menor o preço por aluno. A escola pequena paga mais por aluno: com 100 alunos, o Essencial sai a R$ 90 por aluno por ano. Ainda assim, são R$ 7,50 por mês, menos de 2% de uma mensalidade de R$ 500.</li>
    <li><b>Semestral custa 10% a mais</b> que metade do anual. A escola testa por um semestre, e o anual fica mais vantajoso na renovação.</li>
    <li><b>{M.TESTE_GRATIS_DIAS} dias de teste grátis</b>, sem cartão e com implantação acompanhada. São duas semanas de aula: o professor adapta, usa em sala e vê a reação dos alunos, e a coordenação decide na reunião semanal. O teste custa quase nada para nós: cerca de {reais(R['ia_material'], 2)} de IA por material.</li>
  </ul>
  <h3>Por que a escola paga: o preço volta {br(VAL['retorno'], 1)} vezes</h3>
  <table class="t"><tbody>
    <tr><td>Professores do fundamental numa escola de 200 alunos</td><td class="num">{M.HIPOTESES['professores_por_200']}</td></tr>
    <tr><td>Horas por semana que cada um gasta adaptando material sozinho (hipótese a medir no piloto)</td><td class="num">{br(M.HIPOTESES['horas_por_professor'])} h</td></tr>
    <tr><td>Horas economizadas por mês</td><td class="num">{br(VAL['horas_mes'])} h</td></tr>
    <tr><td>Valor da hora pelo piso nacional de 2026 ({reais(V['piso_professor'], 2)} por 40 horas semanais)</td><td class="num">{reais(VAL['hora'], 2)}</td></tr>
    <tr><td><b>Valor das horas economizadas por mês</b></td><td class="num"><b>{reais(VAL['economia_mes'])}</b></td></tr>
    <tr><td><b>Preço do plano Essencial por mês</b></td><td class="num"><b>{reais(VAL['preco_mes'])}</b></td></tr>
  </tbody></table>
  <p class="destaque">Para uma família que paga de {reais(V['mensalidade_ef'][0][0] if False else 500)} a {reais(2000)} de mensalidade, o PRISMA custa à escola de R$ 3,75 a R$ 5 por aluno por mês: <b>menos de 1% da mensalidade</b>. Usamos o piso salarial, o valor mais baixo possível. Com o salário real da escola particular, o retorno é maior.</p>
</section>

<section class="pagina">
  <p class="eyebrow">5 · Quanto custa entregar</p>
  <h2>Custo baixo por escola, margem alta</h2>
  <table class="t"><thead><tr><th>Item</th><th>Valor</th><th>Como calculamos</th></tr></thead><tbody>
    <tr><td>IA por material adaptado</td><td class="num">{reais(R['ia_material'], 2)}</td><td>Duas páginas, dois níveis de Leitura Fácil, duas imagens descritas e 20% de reenvio, no preço da API Gemini 3.1 Flash-Lite, com dólar a R$ {br(M.HIPOTESES['dolar'], 2)}</td></tr>
    <tr><td>Servidor, IA e suporte por escola ativa</td><td class="num">{reais(M.HIPOTESES['custo_var_escola_mes'])}/mês</td><td>Cobre cerca de 1.000 materiais por mês, muito acima do uso esperado</td></tr>
    <tr><td>Receita média por escola</td><td class="num">{reais(R['ticket_mes'])}/mês</td><td>55% no Essencial, 35% no Escola e 10% no Ampliado, com 40% no semestral</td></tr>
    <tr><td>Impostos e taxas de pagamento</td><td class="num">8% a 13,5%</td><td>Simples Nacional, Anexo III (alíquota efetiva crescente), mais 2% de boleto, PIX e cartão</td></tr>
    <tr><td><b>O que sobra por escola, por mês</b></td><td class="num"><b>{reais(R['margem_contrib_mes'])}</b></td><td>Receita menos impostos, taxas e custo por escola</td></tr>
    <tr><td>Custo para conquistar uma escola</td><td class="num">{reais(M.HIPOTESES['cac'])}</td><td>Comissão de venda, eventos de educação, visita, demonstração e acompanhamento do teste</td></tr>
    <tr><td><b>Esse custo se paga em</b></td><td class="num"><b>{br(R['payback_meses'], 1)} meses</b></td><td>Custo para conquistar ÷ o que sobra por mês</td></tr>
    <tr><td><b>Cada escola rende, em 3 anos</b></td><td class="num"><b>{br(R['ltv_cac'], 1)}×</b></td><td>o que custou para conquistá-la ({reais(R['ltv_36'])} contra {reais(M.HIPOTESES['cac'])})</td></tr>
  </tbody></table>
  <p class="destaque">O custo da IA é tão baixo que <b>não é ele que decide o preço</b>. O preço vem do valor para a escola (as horas de professor) e o custo vem principalmente da equipe e de conquistar escolas.</p>
</section>

<section class="pagina">
  <p class="eyebrow">6 · Projeção de 3 anos (cenário base)</p>
  <h2>Lucro todo mês a partir de {mes_ano(e)}</h2>
  <p>Lançamos em fevereiro de 2027, no começo do ano letivo. As vendas se concentram em fevereiro e março e em julho e agosto, quando as escolas planejam o semestre. Metas de novas escolas: {', '.join(br(x) for x in M.NOVAS_POR_ANO)} em 2027, 2028 e 2029. Supomos que 20% das escolas cancelam por ano.</p>
  {tabela_anos()}
  {linhas("Receita e custos por mês", [("Receita", AZUL, receita), ("Custos", LARANJA, custo)], "modelo do time (modelo.py)", marcar=(e['m'] - 1, f"lucro a partir de {mes_ano(e)}") if e else None)}
  <p>A equipe cresce em degraus: 4 fundadores com ajuda de custo nos primeiros meses, 2 contratações em 2028 (vendas e suporte) e 6 em 2029. Por isso os custos sobem em janeiro de cada ano, e a receita alcança depois.</p>
</section>

<section class="pagina">
  <p class="eyebrow">7 · Investimento e cenários</p>
  <h2>{reais(APORTE)} de investidor-anjo</h2>
  {linhas("Dinheiro acumulado em caixa, mês a mês (cenário base, sem o investimento)", [("Caixa", AZUL, caixa)], "modelo do time (modelo.py)", zero=True, marcar=(R['pior_mes']['m'] - 1, f"pior momento: {reais(R['pior_mes']['caixa'])}"))}
  <p>No cenário base, o caixa chega ao ponto mais baixo em {mes_ano(R['pior_mes'])}, com {reais(R['investimento'])} negativos. Pedimos <b>{reais(APORTE)}</b>: cobre esse valor com cerca de {br(100 * (APORTE / R['investimento'] - 1))}% de folga para atrasos de venda. A participação societária será negociada com o investidor; nossa proposta de partida é 12,5%.</p>
  {uso_recursos()}
  <p>Mais da metade do dinheiro vai para conquistar escolas: vendedor, eventos de educação, visitas e o acompanhamento do teste grátis. O produto já existe e funciona. O que falta é chegar às escolas.</p>
</section>

<section class="pagina">
  <p class="eyebrow">7 · Investimento e cenários (continuação)</p>
  <h2>E se as vendas forem piores?</h2>
  {tabela_cenarios()}
  <p class="destaque">No cenário pessimista, o negócio ainda chega a {br(cen_p['escolas_fim'])} escolas e lucro mensal{(' em ' + mes_ano(cen_p['equilibrio'])) if cen_p['equilibrio'] else ''}, mas precisaria de {reais(cen_p['investimento'])}. Por isso a regra de segurança: se as vendas do 1º semestre de 2027 ficarem abaixo do pessimista, adiamos as contratações de 2028 antes de usar mais dinheiro.</p>
  <h3>Marcos que o investidor pode cobrar</h3>
  {tabela_marcos()}
</section>

<section class="pagina">
  <p class="eyebrow">8 · Riscos e como reduzimos</p>
  <h2>O que pode dar errado</h2>
  <table class="t"><thead><tr><th>Risco</th><th>Como reduzimos</th></tr></thead><tbody>
    <tr><td>A escola não ver valor no teste</td><td>{M.TESTE_GRATIS_DIAS} dias de teste com implantação acompanhada e um relatório de horas economizadas no fim do teste.</td></tr>
    <tr><td>A IA errar</td><td>Nada chega ao aluno sem o professor aprovar. Regras automáticas conferem o texto da IA (frases curtas, sem abreviações) e devolvem para correção.</td></tr>
    <tr><td>O preço da IA subir ou o fornecedor mudar</td><td>Trocar de fornecedor é mudar uma função no código. O custo atual por material é cerca de {reais(R['ia_material'], 2)}: uma alta de 10 vezes ainda caberia no preço.</td></tr>
    <tr><td>Dados de crianças (LGPD)</td><td>Só registramos necessidades de aprendizagem, nunca diagnóstico. Alunos entram com apelido e figurinhas. No plano pago da IA, os dados não treinam o modelo.</td></tr>
    <tr><td>Vendas sazonais</td><td>Vendas concentradas no início de cada semestre, plano semestral para quem quer testar e caixa para os meses de baixa.</td></tr>
    <tr><td>Um concorrente grande copiar</td><td>Nosso diferencial é o Manual: 51 critérios com evidências, que viram regras no código. Some-se o foco no tempo do professor e o preço de entrada baixo.</td></tr>
  </tbody></table>
  <h3>Próximos passos</h3>
  <ol class="lista">
    <li>Piloto gratuito em 3 escolas particulares no 1º semestre de 2027, medindo as horas economizadas.</li>
    <li>Validar com professores e com o AEE os parâmetros do Manual marcados como "a testar".</li>
    <li>Rodada anjo de {reais(APORTE)} para contratar vendas e suporte em 2028.</li>
  </ol>
</section>

<section class="pagina fontes">
  <p class="eyebrow">Fontes e hipóteses</p>
  <h2>De onde vêm os números</h2>
  {fontes_lista()}
  <h3>Hipóteses do time (a validar no piloto)</h3>
  <p>Sobreposição de {br(100 * M.HIPOTESES['sobreposicao'])}% entre as necessidades. {M.HIPOTESES['professores_por_200']} professores por escola de 200 alunos. {br(M.HIPOTESES['horas_por_professor'])} horas por semana de adaptação manual por professor. 20% das escolas cancelam por ano. Custo de {reais(M.HIPOTESES['cac'])} para conquistar uma escola. Dólar a R$ {br(M.HIPOTESES['dolar'], 2)}. Alíquota efetiva do Simples Nacional de 6% a 11,5%. Todos os cálculos estão em <span class="mono">pitch/plano-negocio/modelo.py</span>: mude uma hipótese e gere o PDF de novo.</p>
</section>
</body></html>"""


CSS = """
@page { size: A4; margin: 16mm 17mm 18mm; }
:root { --ink:#1E2235; --muted:#4A4F6A; --line:#D9D3C4; --soft:#F3EDDF; --blue:#1F6FB2; --laranja:#A3401F; --sol:#FFC93C; --papel:#FBF7EE;
  --display:'Pixelify Sans','Atkinson Hyperlegible Next',system-ui,sans-serif; --body:'Atkinson Hyperlegible Next',system-ui,sans-serif; --mono:'Departure Mono',ui-monospace,monospace; }
* { box-sizing:border-box; }
body { margin:0; color:var(--ink); background:#fff; font:11pt/1.55 var(--body); }
h1,h2,h3 { font-family:var(--display); font-weight:400; line-height:1.2; margin:0 0 8pt; }
h2 { font-size:19pt; margin-bottom:12pt; }
h3 { font-size:13pt; margin:14pt 0 6pt; }
p { margin:0 0 8pt; }
.pagina { break-before:page; }
.eyebrow { font-family:var(--mono); font-size:9.5pt; letter-spacing:.06em; color:var(--blue); margin:0 0 4pt; }
.mono { font-family:var(--mono); font-size:.92em; }
.capa { min-height:255mm; display:flex; flex-direction:column; justify-content:center; padding:10mm 4mm; background:var(--papel); border:3px solid var(--ink); }
.capa h1 { font-size:58pt; margin:6pt 0 2pt; color:var(--ink); }
.capa .sigla { font-size:13pt; color:var(--muted); }
.capa .lema { font-family:var(--display); font-size:19pt; margin:18pt 0 26pt; }
.capa-numeros { list-style:none; padding:0; margin:0 0 28pt; display:grid; grid-template-columns:repeat(2,1fr); gap:10pt; }
.capa-numeros li { background:#fff; border:2px solid var(--ink); padding:10pt 12pt; display:grid; gap:2pt; }
.capa-numeros b { font-size:22pt; font-family:var(--body); }
.capa-numeros span { color:var(--muted); font-size:10.5pt; }
.capa .time { color:var(--muted); font-size:10.5pt; margin-top:auto; }
.bloco { border-left:4pt solid var(--blue); padding:2pt 0 2pt 10pt; margin-bottom:10pt; break-inside:avoid; }
.bloco h3 { margin-top:0; }
.duas { display:grid; grid-template-columns:1fr 1fr; gap:14pt; align-items:start; }
figure { margin:0 0 14pt; break-inside:avoid; }
.grafico { width:100%; height:auto; font-family:var(--body); }
figcaption.tit { font-family:var(--display); font-weight:400; font-size:11.5pt; margin-bottom:6pt; }
figcaption.fonte { font-size:8.5pt; color:var(--muted); margin-top:4pt; }
.rosca-grade { display:grid; grid-template-columns:58mm 1fr; gap:14pt; align-items:center; }
.leg-rosca { list-style:none; padding:0; margin:0; font-size:10pt; }
.leg-rosca li { display:grid; grid-template-columns:12pt 1fr auto 24mm; gap:6pt; align-items:baseline; padding:3pt 0; border-top:1px solid var(--line); }
.leg-rosca i { width:10pt; height:10pt; display:inline-block; transform:translateY(1pt); outline:1.5pt solid var(--ink); }
.leg-rosca b { font-variant-numeric:tabular-nums; }
.leg-rosca em { font-style:normal; color:var(--muted); text-align:right; font-variant-numeric:tabular-nums; }
.medidor .trilho { height:24pt; background:var(--soft); border:1px solid var(--line); overflow:hidden; }
.medidor .trilho span { display:flex; align-items:center; justify-content:flex-end; height:100%; background:var(--ink); color:#fff; padding-right:6pt; font-size:10pt; }
.med-leg { display:flex; flex-wrap:wrap; gap:4pt 14pt; font-size:9.5pt; margin-top:4pt; }
.legenda { list-style:none; padding:0; margin:0 0 4pt; display:flex; gap:16pt; font-size:10pt; }
.legenda i { display:inline-block; width:10pt; height:10pt; margin-right:5pt; outline:1.5pt solid var(--ink); transform:translateY(1pt); }
.t { width:100%; border-collapse:collapse; font-size:10pt; margin:4pt 0 12pt; break-inside:avoid; }
.t th { text-align:left; font-weight:700; border-bottom:2px solid var(--ink); padding:5pt 6pt; vertical-align:bottom; }
.t td { border-bottom:1px solid var(--line); padding:5pt 6pt; vertical-align:top; }
.t .num { text-align:right; white-space:nowrap; font-variant-numeric:tabular-nums; }
.t .neg { color:var(--laranja); }
.t .sub { display:block; color:var(--muted); font-size:9pt; }
.destaque { background:var(--soft); border:2px solid var(--ink); padding:8pt 10pt; break-inside:avoid; }
.cartoes { list-style:none; padding:0; margin:0 0 10pt; display:grid; grid-template-columns:repeat(3,1fr); gap:10pt; }
.cartoes li { border:2px solid var(--ink); padding:10pt; display:grid; gap:4pt; align-content:start; }
.cartoes b { font-size:15pt; }
.cartoes span { font-size:10pt; color:var(--muted); }
.cartoes em { font-style:normal; font-family:var(--mono); font-size:9pt; color:var(--blue); }
.lista { padding-left:16pt; }
.lista li { margin-bottom:5pt; }
.fontes ol { font-size:9pt; padding-left:16pt; }
.fontes li { margin-bottom:3pt; }
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
        pg.pdf(path=str(destino), format="A4", print_background=True, display_header_footer=True,
               header_template="<span></span>",
               footer_template='<div style="width:100%;font:8px sans-serif;color:#4A4F6A;padding:0 17mm;display:flex;justify-content:space-between">'
                               '<span>PRISMA · Plano de negócio · Time Carcará 3301</span><span><span class="pageNumber"></span> de <span class="totalPages"></span></span></div>',
               margin={"top": "16mm", "bottom": "18mm", "left": "17mm", "right": "17mm"})
        nav.close()
    print("ok:", destino)


if __name__ == "__main__":
    main()
