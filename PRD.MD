# PRD — Motor de Reembolso de Despesas

**Versão:** 0.1 · **Status:** rascunho · **Data:** 2026-10-15

## Resumo

O produto é um motor de cálculo que avalia despesas corporativas de um
colaborador em um período segundo uma política de reembolso. Ele recebe um
arquivo JSON e produz outro JSON com o valor reembolsável e uma justificativa
para cada decisão.

## Problema

Hoje o financeiro confere manualmente cada despesa em uma planilha, compara os
itens com a política e devolve aprovações e recusas. Esse processo demora e está
sujeito a erros e inconsistências.

## Usuários e necessidade

- **Financeiro:** precisa avaliar despesas de forma consistente e entender o
  motivo de cada decisão.
- **Colaborador:** precisa receber um resultado rastreável para as despesas
  submetidas.

## Objetivo

Reduzir o esforço de conferência manual e tornar cada cálculo reproduzível,
explicável e verificável contra as regras documentadas.

## Fluxo principal

1. O operador fornece um JSON com os dados do colaborador, período e despesas.
2. O produto avalia cada despesa segundo a política documentada.
3. O produto grava um JSON de resultado no caminho indicado, contendo o valor
   reembolsável e a justificativa de cada decisão.

## Requisitos conhecidos

- A interface do produto é uma CLI com o formato
  `<comando> calcular --input despesas.json --output resultado.json`.
- A entrada respeita o formato exemplificado em
  `exemplos/despesas-exemplo.json`.
- A saída é JSON e seu schema será definido na spec.
- A política define limites-base para alimentação, transporte urbano e
  hospedagem, reembolso parcial acima do limite, exigência de nota fiscal,
  ampliação de limites para viagem, restrição de competência, tratamento de
  duplicatas e recusa de categorias fora da política.
- Testes automatizados são obrigatórios.
- O comportamento detalhado das regras é governado por
  `specs/001-motor-reembolso/spec.md`, não por este resumo.

## Critérios de sucesso

- Um operador consegue executar o cálculo seguindo o README do produto.
- O resultado pode ser lido como JSON e explica a decisão para cada despesa.
- As regras desambiguadas da spec são cobertas por testes automatizados.
- Dado o mesmo arquivo e a mesma política, o produto apresenta resultado
  consistente, conforme contrato a definir na spec.

## Fora do produto nesta entrega

- Execução de pagamentos ou integração bancária.
- Fluxo de aprovação humana ou gestão de solicitações.
- Interface gráfica, autenticação e gestão de usuários.
- Persistência ou integração com sistemas corporativos.
- Interface de administração da política.

## Decisões pendentes

As interpretações da política, schema de saída, tratamento de dados inválidos,
stack e comandos de execução estão em `pendencias.MD`. Não são requisitos
fechados até serem decididos e registrados nos documentos apropriados.