"""Modelo do plano de negócio do PRISMA: público, mercado, preço e finanças (36 meses).

Uso:  python pitch/plano-negocio/modelo.py        (imprime o resumo)
Todo número de entrada está em DADOS (com fonte) ou em HIPOTESES (decisão do time, a validar).
Mudou uma hipótese? Rode de novo: o PDF (gerar_pdf.py) lê tudo daqui.
"""
from __future__ import annotations

# ---------------- dados com fonte ----------------
DADOS = {
    "ef_matriculas": (25_800_000, "INEP, Censo Escolar 2025 (Agência Gov, ago/2026)"),
    "ef_privada_iniciais": (2_840_000, "INEP, Censo Escolar 2024 via Fenep: 19,6% dos anos iniciais"),
    "ef_privada_finais": (1_950_000, "INEP, Censo Escolar 2024 via Fenep: 17,0% dos anos finais"),
    "escolas_ef_privadas": (24_683, "INEP, Notas Estatísticas do Censo Escolar 2025"),
    "escolas_ef_total": (119_244, "INEP, Notas Estatísticas do Censo Escolar 2025"),
    "educ_especial_total": (2_500_000, "INEP, Notas Estatísticas do Censo Escolar 2025"),
    "educ_especial_parte_ef": (0.629, "INEP, Censo Escolar 2023: 62,9% das matrículas de educação especial estão no fundamental"),
    "tdah": (0.051, "Arruda, Querido, Bigal e Polanczyk (2015), 1.830 crianças de 5 a 13 anos"),
    "dislexia": (0.05, "Associação Brasileira de Dislexia (estimativa mais conservadora; a literatura vai de 5% a 17%)"),
    "daltonismo_meninos": (0.08, "American Optometric Association, citada por Alves e Alves (UniFOA, 2025)"),
    "daltonismo_meninas": (0.005, "American Optometric Association, citada por Alves e Alves (UniFOA, 2025)"),
    "meninos": (0.506, "INEP, Censo Escolar 2025: 50,6% das matrículas"),
    "saeb_5_lp": (0.607, "Saeb 2025, Todos Pela Educação (ago/2026): aprendizado adequado"),
    "saeb_5_mt": (0.506, "Saeb 2025, Todos Pela Educação (ago/2026): aprendizado adequado"),
    "saeb_9_lp": (0.383, "Saeb 2025, Todos Pela Educação (ago/2026): aprendizado adequado"),
    "saeb_9_mt": (0.188, "Saeb 2025, Todos Pela Educação (ago/2026): aprendizado adequado"),
    "alfabetizadas_2ano": (0.592, "MEC, Indicador Criança Alfabetizada 2024"),
    "fundeb_vaaf_min": (5_962.79, "Portaria Interministerial nº 14/2025 (estimativa do VAAF-MIN 2026)"),
    "piso_professor": (5_130.63, "MEC, Portaria nº 82/2026: piso de 40 horas semanais"),
    "mensalidade_ef": ((500, 2_000), "Melhor Escola (2026): faixa típica do fundamental"),
    "gemini_entrada_usd_m": (0.25, "Google, preços da API Gemini 3.1 Flash-Lite (por milhão de tokens)"),
    "gemini_saida_usd_m": (1.50, "Google, preços da API Gemini 3.1 Flash-Lite (por milhão de tokens)"),
}
V = {k: v[0] for k, v in DADOS.items()}

# ---------------- hipóteses do time (a validar no piloto) ----------------
HIPOTESES = {
    "sobreposicao": 0.15,          # parte dos alunos com mais de uma necessidade (ex.: TDAH e dislexia juntos)
    "dolar": 5.50,                 # câmbio usado para o custo da IA
    "horas_por_professor": 2.0,    # horas por semana que o professor gasta adaptando material sozinho
    "professores_por_200": 12,     # professores do fundamental numa escola de 200 alunos
    "semanas_mes": 4.3,
    "acrescimo_semestral": 0.10,   # o semestral custa 10% a mais que metade do anual
    "parte_semestral": 0.40,       # escolas que preferem pagar por semestre
    "mix": {"essencial": 0.55, "escola": 0.35, "ampliado": 0.10},  # média de 194 alunos por escola privada
    "churn_mes": 0.0185,           # cerca de 20% das escolas saem por ano (conservador)
    "cac": 6_000,                  # custo para conquistar uma escola: comissão, eventos, visita, demonstração e acompanhamento do teste
    "custo_var_escola_mes": 80,    # IA, armazenamento e suporte por escola ativa
    "taxa_pagamento": 0.02,        # boleto, PIX e cartão
}

PLANOS = {  # preço anual com âncora de R$ 60 por aluno por ano (na faixa central de cada plano)
    "essencial": {"nome": "Essencial", "faixa": "até 200 alunos", "ref": 150, "anual": 9_000},
    "escola": {"nome": "Escola", "faixa": "201 a 500 alunos", "ref": 350, "anual": 21_000},
    "ampliado": {"nome": "Ampliado", "faixa": "501 a 1.000 alunos", "ref": 750, "anual": 45_000},
}
TESTE_GRATIS_DIAS = 14  # duas semanas de aula: adaptar, usar em sala e a coordenação decidir

# lançamento em janeiro de 2027; peso de cada mês nas novas assinaturas (início de ano e de semestre vendem mais)
INICIO_ANO, MESES = 2027, 36
SAZONAL = [0.0, 1.6, 1.4, 0.8, 0.6, 0.5, 1.4, 1.3, 0.7, 0.6, 0.5, 0.4]
NOVAS_POR_ANO = [25, 100, 250]
CUSTOS_FIXOS = [  # por mês, em cada ano: equipe, infraestrutura, administração, marketing
    {"equipe": None, "infra": 600, "admin": 1_500, "marketing": 3_000},
    {"equipe": 32_000, "infra": 1_800, "admin": 3_000, "marketing": 6_000},
    {"equipe": 75_000, "infra": 4_500, "admin": 6_000, "marketing": 15_000},
]
EQUIPE_ANO1 = [4_000] * 6 + [12_000] * 6      # ajuda de custo nos 6 primeiros meses, depois pró-labore
IMPOSTO = [0.06, 0.09, 0.115]                 # Simples Nacional, Anexo III (alíquota efetiva crescente)


# ---------------- público ----------------
def publico() -> dict:
    ef = V["ef_matriculas"]
    especial = V["educ_especial_total"] * V["educ_especial_parte_ef"]
    tdah = ef * V["tdah"]
    dislexia = ef * V["dislexia"]
    dalt = ef * (V["meninos"] * V["daltonismo_meninos"] + (1 - V["meninos"]) * V["daltonismo_meninas"])
    soma = especial + tdah + dislexia + dalt
    nucleo = soma * (1 - HIPOTESES["sobreposicao"])
    sem_lp = 1 - (V["saeb_5_lp"] + V["saeb_9_lp"]) / 2
    dificuldade = ef * sem_lp
    privada = V["ef_privada_iniciais"] + V["ef_privada_finais"]
    return {
        "ef": ef, "especial": especial, "tdah": tdah, "dislexia": dislexia, "daltonismo": dalt,
        "soma": soma, "nucleo": nucleo, "nucleo_pct": nucleo / ef,
        "sem_lp": sem_lp, "dificuldade": dificuldade,
        "privada": privada, "privada_pct": privada / ef,
        "privada_nucleo": privada * nucleo / ef,
        "alunos_por_escola_privada": privada / V["escolas_ef_privadas"],
    }


# ---------------- preço ----------------
def planos() -> dict:
    out = {}
    for k, p in PLANOS.items():
        semestre = p["anual"] / 2 * (1 + HIPOTESES["acrescimo_semestral"])
        out[k] = {**p, "mes_equivalente": p["anual"] / 12, "semestre": semestre,
                  "por_aluno_ano_ref": p["anual"] / p["ref"]}
    return out


def ticket_medio_anual() -> float:
    base = sum(HIPOTESES["mix"][k] * PLANOS[k]["anual"] for k in PLANOS)
    return base * (1 + HIPOTESES["parte_semestral"] * HIPOTESES["acrescimo_semestral"])


def custo_ia_por_material() -> float:
    """Material de 2 páginas: Leitura Fácil I e II, duas imagens descritas e 20% de reenvio."""
    entrada, saida = 8_000 * 1.2, 5_500 * 1.2
    usd = entrada / 1e6 * V["gemini_entrada_usd_m"] + saida / 1e6 * V["gemini_saida_usd_m"]
    return usd * HIPOTESES["dolar"]


def valor_para_escola() -> dict:
    """Horas de professor que a escola deixa de gastar adaptando material, no plano Essencial."""
    hora = V["piso_professor"] / (40 * HIPOTESES["semanas_mes"])
    horas = HIPOTESES["professores_por_200"] * HIPOTESES["horas_por_professor"] * HIPOTESES["semanas_mes"]
    economia = horas * hora
    preco = PLANOS["essencial"]["anual"] / 12
    return {"hora": hora, "horas_mes": horas, "economia_mes": economia, "preco_mes": preco, "retorno": economia / preco}


# ---------------- finanças mês a mês ----------------
CENARIOS = {  # multiplicadores sobre a base: novas escolas, cancelamento e custo de aquisição
    "pessimista": {"novas": 0.6, "churn": 1.5, "cac": 1.5},
    "base": {"novas": 1.0, "churn": 1.0, "cac": 1.0},
    "otimista": {"novas": 1.4, "churn": 0.7, "cac": 0.8},
}


def projecao(cenario: str = "base") -> list[dict]:
    c = CENARIOS[cenario]
    ticket_mes = ticket_medio_anual() / 12
    ativas, caixa, linhas = 0.0, 0.0, []
    for m in range(MESES):
        ano, mes = divmod(m, 12)
        novas = NOVAS_POR_ANO[ano] * c["novas"] * SAZONAL[mes] / sum(SAZONAL)
        saidas = ativas * HIPOTESES["churn_mes"] * c["churn"]
        ativas = ativas + novas - saidas
        receita = ativas * ticket_mes
        fixos = dict(CUSTOS_FIXOS[ano])
        fixos["equipe"] = EQUIPE_ANO1[mes] if ano == 0 else fixos["equipe"]
        variaveis = (receita * (IMPOSTO[ano] + HIPOTESES["taxa_pagamento"])
                     + ativas * HIPOTESES["custo_var_escola_mes"] + novas * HIPOTESES["cac"] * c["cac"])
        custo = sum(fixos.values()) + variaveis
        resultado = receita - custo
        caixa += resultado
        detalhe = {
            "Equipe": fixos["equipe"],
            "Conquista de escolas": novas * HIPOTESES["cac"] * c["cac"] + fixos["marketing"],
            "Impostos e taxas": receita * (IMPOSTO[ano] + HIPOTESES["taxa_pagamento"]),
            "Servidores, IA e suporte": fixos["infra"] + ativas * HIPOTESES["custo_var_escola_mes"],
            "Administração e jurídico": fixos["admin"],
        }
        linhas.append({"m": m + 1, "ano": INICIO_ANO + ano, "mes": mes + 1, "novas": novas, "ativas": ativas,
                       "receita": receita, "custo": custo, "fixos": sum(fixos.values()), "variaveis": variaveis,
                       "resultado": resultado, "caixa": caixa, "detalhe": detalhe})
    return linhas


def indicadores(lin: list[dict]) -> dict:
    equilibrio = next((l for i, l in enumerate(lin) if all(x["resultado"] >= 0 for x in lin[i:])), None)
    pior = min(lin, key=lambda l: l["caixa"])
    return {"equilibrio": equilibrio, "investimento": max(0.0, -pior["caixa"]), "pior_mes": pior,
            "escolas_fim": lin[-1]["ativas"], "arr_fim": lin[-1]["receita"] * 12, "caixa_fim": lin[-1]["caixa"]}


def resumo() -> dict:
    p, lin = publico(), projecao()
    ticket = ticket_medio_anual()
    mes_cm = ticket / 12 * (1 - IMPOSTO[1] - HIPOTESES["taxa_pagamento"]) - HIPOTESES["custo_var_escola_mes"]
    equilibrio = next((l for i, l in enumerate(lin) if all(x["resultado"] >= 0 for x in lin[i:])), None)
    anos = []
    for a in range(3):
        bloco = lin[a * 12:(a + 1) * 12]
        anos.append({"ano": INICIO_ANO + a, "receita": sum(l["receita"] for l in bloco), "custo": sum(l["custo"] for l in bloco),
                     "resultado": sum(l["resultado"] for l in bloco), "escolas_fim": bloco[-1]["ativas"],
                     "arr_fim": bloco[-1]["receita"] * 12})
    return {
        "publico": p, "planos": planos(), "ticket_anual": ticket, "ticket_mes": ticket / 12,
        "margem_contrib_mes": mes_cm, "payback_meses": HIPOTESES["cac"] / mes_cm,
        "ltv_36": mes_cm * 36, "ltv_cac": mes_cm * 36 / HIPOTESES["cac"],
        "ia_material": custo_ia_por_material(), "valor": valor_para_escola(),
        "tam": p["ef"] * 60, "sam": p["privada"] * 60,
        "som_escolas": anos[-1]["escolas_fim"], "som_parte": anos[-1]["escolas_fim"] / V["escolas_ef_privadas"],
        "anos": anos, "equilibrio": equilibrio, "investimento": -min(l["caixa"] for l in lin),
        "pior_mes": min(lin, key=lambda l: l["caixa"]), "linhas": lin,
        "cenarios": {k: {**indicadores(projecao(k)), "linhas": projecao(k)} for k in CENARIOS},
        "fundeb_parte": 60 / V["fundeb_vaaf_min"],
    }


def br(x, casas=0):
    s = f"{x:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


if __name__ == "__main__":
    r = resumo()
    p = r["publico"]
    print("PÚBLICO (ensino fundamental)")
    for k in ("ef", "especial", "tdah", "dislexia", "daltonismo", "soma", "nucleo", "dificuldade", "privada", "privada_nucleo"):
        print(f"  {k:16s} {br(p[k])}")
    print(f"  núcleo = {br(100*p['nucleo_pct'],1)}% do fundamental | sem aprendizado adequado em português (média 5º e 9º) = {br(100*p['sem_lp'],1)}%")
    print(f"  alunos por escola privada com fundamental: {br(p['alunos_por_escola_privada'])}")
    print("PLANOS")
    for k, x in r["planos"].items():
        print(f"  {x['nome']:9s} {x['faixa']:18s} anual R$ {br(x['anual'])} | semestre R$ {br(x['semestre'])} | mês equiv. R$ {br(x['mes_equivalente'])} | R$ {br(x['por_aluno_ano_ref'])}/aluno/ano em {x['ref']} alunos")
    print(f"TICKET médio anual R$ {br(r['ticket_anual'])} | mensal R$ {br(r['ticket_mes'])}")
    print(f"UNIDADE margem/mês R$ {br(r['margem_contrib_mes'])} | CAC R$ {br(HIPOTESES['cac'])} | payback {br(r['payback_meses'],1)} meses | LTV 36m R$ {br(r['ltv_36'])} | LTV/CAC {br(r['ltv_cac'],1)}")
    print(f"IA por material R$ {br(r['ia_material'],2)}")
    v = r["valor"]
    print(f"VALOR escola Essencial: {br(v['horas_mes'])} h/mês × R$ {br(v['hora'],2)} = R$ {br(v['economia_mes'])} contra R$ {br(v['preco_mes'])} → {br(v['retorno'],1)}x")
    print(f"MERCADO TAM R$ {br(r['tam']/1e6,1)} mi/ano | SAM (privadas) R$ {br(r['sam']/1e6,1)} mi/ano | fim do ano 3: {br(r['som_escolas'])} escolas = {br(100*r['som_parte'],2)}% das privadas com fundamental")
    for a in r["anos"]:
        print(f"  {a['ano']}: receita R$ {br(a['receita'])} | custo R$ {br(a['custo'])} | resultado R$ {br(a['resultado'])} | escolas no fim {br(a['escolas_fim'])} | receita anual recorrente R$ {br(a['arr_fim'])}")
    e = r["equilibrio"]
    print(f"EQUILÍBRIO: mês {e['m']} ({e['mes']:02d}/{e['ano']}) com {br(e['ativas'])} escolas" if e else "EQUILÍBRIO: não atinge em 36 meses")
    print(f"INVESTIMENTO necessário (pior caixa acumulado): R$ {br(r['investimento'])} em {r['pior_mes']['mes']:02d}/{r['pior_mes']['ano']}")
    print(f"R$ 60/aluno/ano = {br(100*r['fundeb_parte'],2)}% do Fundeb mínimo por aluno")
    for k, c in r["cenarios"].items():
        e = c["equilibrio"]
        print(f"CENÁRIO {k:10s} equilíbrio {('%02d/%d' % (e['mes'], e['ano'])) if e else 'não atinge':>10s} | investimento R$ {br(c['investimento'])} | escolas fim R$ {br(c['escolas_fim'])} | receita anual recorrente R$ {br(c['arr_fim'])} | caixa acumulado R$ {br(c['caixa_fim'])}")
