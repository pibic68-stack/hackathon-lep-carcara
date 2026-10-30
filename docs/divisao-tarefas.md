# Divisão de tarefas

Regra de ouro: **ninguém espera ninguém.** Cada frente começa agora com dados de exemplo
e se conecta às outras depois. A pesquisa *melhora* o trabalho dos outros, mas não o *bloqueia*.

## Contratos entre as frentes (combinar nos primeiros 30 min)

Para trabalharem em paralelo, todos precisam concordar em **dois formatos**:

**1. Perfil do aluno** (`relatorios/exemplos/perfil-exemplo.json`)
```json
{
  "aluno": "Aluno Fictício A",
  "serie": "5º ano",
  "necessidades": ["baixa_visao", "instrucoes_em_etapas"],
  "preferencias": ["audio", "fonte_ampliada"],
  "observacoes_professor": "Se distrai com páginas muito cheias."
}
```

**2. Regra de adaptação** (cada linha do Manual vira uma destas)
```json
{
  "id": "R-DALT-01",
  "necessidade": "daltonismo",
  "regra": "Toda informação em cor deve vir acompanhada de símbolo ou palavra.",
  "como_aplicar": "Adicionar rótulo de texto a gráficos e legendas coloridas.",
  "fonte": "WCAG 2.2, critério 1.4.1"
}
```

---

## 👤 Pessoa 1: Pesquisa e Manual
**Objetivo:** responder "quais barreiras os alunos PCD enfrentam e o que funciona para cada uma?"

- [ ] Completar `docs/pesquisa/matriz-barreiras.md` (o rascunho já está lá)
- [ ] **Entregar primeiro as 3 necessidades da demo** (sugestão: baixa visão, daltonismo, TEA), depois as outras
- [ ] Converter cada adaptação em uma regra no formato acima → `docs/manual/padroes.json` (feito na v1.0)
- [ ] Separar 5 a 8 dados de impacto com fonte para o pitch → `docs/pesquisa/dados-pitch.md`
- [ ] Se possível: conversar com 1 professor ou profissional do AEE e anotar as dores reais

## 👤 Pessoa 2: IA e Backend (Python)
**Objetivo:** recebe material + perfil → devolve versões adaptadas.

- [ ] Ler texto e PDF de uma aula (`backend/`)
- [ ] Implementar as **regras determinísticas** primeiro (não precisa de IA e sempre funciona):
  fonte ampliada, alto contraste, cor + símbolo, quebrar instruções em etapas
- [ ] Depois, usar a IA para: simplificar o texto, descrever imagens, gerar o roteiro de áudio
- [ ] Ler os critérios de `docs/manual/padroes.json` em vez de deixar tudo fixo no código
- [ ] Ter **saída em cache** para a demo não depender da internet ao vivo

## 👤 Pessoa 3: Frontend e Acessibilidade (HTML)
**Objetivo:** as telas que o jurado vai ver.

- [ ] Esboço no papel de 3 telas: **(a)** perfil do aluno (checklist de necessidades), **(b)** envio do material,
      **(c)** resultado: original e adaptado lado a lado
- [ ] Construir em `web/` com dados falsos (não precisa esperar o backend)
- [ ] A interface precisa passar em: contraste, navegação por teclado, textos alternativos
- [ ] Conectar ao backend quando ele estiver pronto

## 👤 Pessoa 4: Relatórios, Dados e Pitch
**Objetivo:** o "guia para professores e famílias" e a história da apresentação.

- [ ] Criar 3 alunos fictícios com perfis diferentes (`relatorios/exemplos/`)
- [ ] Modelo do **guia do professor** e do **guia da família** em LaTeX (`relatorios/modelo/`):
      o que adaptar, como avaliar, o que fazer em casa, em linguagem simples
- [ ] Juntar 2 ou 3 materiais de aula reais (de domínio público) para a demo
- [ ] Roteiro do pitch (`pitch/roteiro.md`): problema → persona → demo → impacto → próximo passo

---

## Marcos

| Quando | O que precisa existir |
|---|---|
| 10% do tempo | Frase do pitch, persona e os 2 formatos JSON combinados |
| 50% | Demo feia funcionando do começo ao fim com 1 aluno e 1 material |
| 80% | 3 perfis funcionando, guia gerado e validado com alguém de fora |
| Final | Pitch ensaiado 3 vezes + vídeo da demo como plano B |
