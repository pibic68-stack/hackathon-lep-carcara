# Plano de negócio do PRISMA

O PDF para a banca é `plano-de-negocio-prisma.pdf`: 27 slides em 16:9. Ele é **gerado**: não edite o PDF à mão.

| Arquivo | Para que serve |
|---|---|
| `modelo.py` | Todos os números: dados com fonte (`DADOS`), hipóteses do time (`HIPOTESES`), planos, cenários e a projeção de 36 meses. |
| `gerar_pdf.py` | Monta o PDF com os textos, as tabelas e os gráficos. Reaproveita os gráficos do Manual (`docs/manual/build_manual.py`). |

## Como mudar um número

1. Abra `modelo.py` e mude o valor (por exemplo, o preço de um plano em `PLANOS` ou as metas em `NOVAS_POR_ANO`).
2. Confira o resumo: `python pitch/plano-negocio/modelo.py`
3. Gere o PDF de novo: `python pitch/plano-negocio/gerar_pdf.py`

O PDF usa o pacote `playwright` (`pip install playwright`) e o Microsoft Edge já instalado no Windows.

## Decisões do time (31/10/2026)

- **Cobrança:** preço fixo por tamanho da escola, em 3 planos, com âncora de R$ 60 por aluno por ano no meio de cada faixa.
  Essencial (até 200 alunos) R$ 9.000/ano; Escola (201 a 500) R$ 21.000; Ampliado (501 a 1.000) R$ 45.000.
  O semestral custa 10% a mais que metade do anual.
- **Teste grátis:** 14 dias, com implantação acompanhada.
- **Primeiro cliente:** escolas particulares com ensino fundamental. Redes públicas a partir de 2029.
- **Investimento:** R$ 500 mil de investidor-anjo (cenário base precisa de cerca de R$ 393 mil).

## O que ainda é hipótese (validar no piloto)

As horas que o professor gasta adaptando material (2 h por semana), a taxa de cancelamento (20% ao ano),
o custo para conquistar uma escola (R$ 6.000) e a sobreposição entre necessidades (15%). Todas estão em `HIPOTESES`.
