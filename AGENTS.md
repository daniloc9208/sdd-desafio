# AGENTS.md

Este arquivo orienta o agente de código usado neste repositório. Mantenha as
instruções curtas e atualizadas.

## O projeto

Motor de cálculo de reembolso de despesas corporativas. A interface exigida é
uma CLI que lê um JSON de despesas e emite um JSON com o resultado e a
justificativa de cada decisão.

## Fonte da verdade

`specs/001-motor-reembolso/spec.md` define **o que** o sistema faz.
`PRD.MD` resume o problema e o produto desejado.
`specs/001-motor-reembolso/plan.md` define **como**.
`specs/001-motor-reembolso/tasks.md` define **em que ordem**.

Quando o código e a spec discordarem, a spec está certa e o código é o bug —
a menos que a spec esteja errada, e nesse caso corrigimos a spec primeiro e
registramos em `DECISIONS.md`.

**Antes de implementar qualquer coisa, leia a task correspondente em `tasks.md`.**
Se o que foi pedido não estiver coberto por uma task, sinalize isso antes de
implementar. Se a task exigir uma decisão de negócio que a spec não registra,
pare e peça que a spec e `DECISIONS.md` sejam atualizados primeiro.

## Regras de trabalho

- Toda regra de negócio vive na spec, não apenas no chat ou em comentário de código.
- Não escolha silenciosamente uma interpretação para uma ambiguidade. Registre a
  pergunta em `pendencias.MD` e solicite a decisão do responsável pelo produto.
- Mudanças na spec devem ser justificadas em `DECISIONS.md`.
- Todo commit de implementação referencia uma task: `feat(T-003): <descrição>`;
  testes podem usar `test(T-003): <descrição>`. Documentação usa `docs(spec):`,
  `docs(plan):` ou `docs(tasks):`, conforme aplicável.
- Nenhuma regra de negócio entra sem teste.
- Não invente evidências, decisões ou conteúdo de sessões. Registre no relatório
  apenas o que ocorreu e pode ser verificado no repositório.

## Stack e comandos

- Python 3.11+; pacote em `src/reembolso`, instalado em modo editável.
- Configurar ambiente: `python -m pip install -e ".[dev]"`
- Executar: `reembolso calcular --input despesas.json --output resultado.json --policy politica.json --exchange-rates cambio.json`
- Testes: `python -m pytest`
- Lint: `ruff check .`
- Formatação (verificação): `ruff format --check .`

## Convenções de código

- Mantenha regras de negócio no núcleo de cálculo, separadas da leitura e escrita
  de arquivos, conforme o plano técnico.
- Use `decimal.Decimal` para valores monetários e câmbio; não use `float` em
  cálculos de reembolso.
- Aplique arredondamento monetário apenas conforme definido na spec.
- Use pytest e associe cada teste de regra ao ID RN correspondente.
- Siga os critérios de aceite e a ordem de aplicação definidos na spec.

## Fora de escopo

- Não acrescente funcionalidades que não estejam na spec ou em uma task aprovada.
- A lista detalhada de exclusões do produto será consolidada na spec.
