# Pendências do Produto

Este arquivo reúne decisões e informações que dependem do responsável pelo
produto. Responda cada item; depois, as decisões de negócio devem ser
registradas na spec e no `DECISIONS.md` antes de orientar implementação.

## Decisões de negócio

- [ ] **AMB-001 — Limite diário:** o teto de alimentação/transporte vale por
  despesa ou pela soma da mesma categoria no dia? Se a soma ultrapassar o teto,
  como distribuir o valor reembolsável entre os itens?
- [ ] **AMB-002 — Reembolso parcial:** acima do limite, reembolsa-se até o teto
  e corta-se o excedente, ou se aplica outra interpretação? Como se aplica
  quando o limite diário é compartilhado?
- [ ] **AMB-003 — Nota fiscal:** despesa exatamente igual a R$ 100 exige nota?
  O que ocorre quando a nota exigida não existe: recusa integral, parcial ou
  outro tratamento?
- [ ] **AMB-004 — Viagem:** como se identifica que o colaborador está em viagem,
  já que esse dado não aparece no JSON de exemplo? Qual o alcance temporal da
  condição de viagem?
- [ ] **AMB-005 — Competência:** a despesa é elegível pela data da despesa, pela
  data de lançamento ou por outra data? Como `competencia`, `inicio` e `fim` se
  relacionam? As datas de início e fim são inclusivas?
- [ ] **AMB-006 — Duplicatas:** quais campos tornam duas despesas duplicatas?
  Qual ocorrência deve prevalecer e como as demais devem aparecer no resultado?
- [ ] **AMB-007 — Categorias:** nomes de categoria ignoram caixa e espaços? Como
  a decisão de categoria fora da política deve ser explicada?
- [ ] **AMB-008 — Hospedagem:** como determinar o número de diárias? A entrada
  deve ganhar um campo para isso ou será adotada outra regra explícita?
- [ ] **AMB-009 — Valores negativos/estornos:** o que significa o valor negativo
  do exemplo e como ele afeta o reembolso?
- [ ] **AMB-010 — Precisão monetária:** como arredondar valores com mais de duas
  casas decimais e em qual etapa do cálculo?
- [ ] **Caso de sábado:** a política não especifica restrições por dia da semana.
  A despesa de sábado segue as mesmas regras dos demais dias?
- [ ] **Ordem de aplicação:** quando várias regras incidirem sobre a mesma
  despesa, qual prevalece e como isso afeta o resultado?

## Contratos e validação

- [ ] Definir o schema de saída: campos, tipos, totais, status e formato das
  justificativas.
- [ ] Definir quais campos da entrada são obrigatórios e como tratar campo
  ausente, tipo inválido, data inválida, valor zero, ID repetido e JSON malformado.
- [ ] Definir se a CLI deve sobrescrever arquivo de saída existente e qual
  comportamento/retorno ocorre em erros de leitura ou cálculo.

## Execução e entrega

- [ ] Escolher stack que o responsável domina e registrar a decisão em
  `specs/001-motor-reembolso/plan.md`.
- [ ] Definir comandos de execução, teste e, se aplicável, lint/format para
  atualizar `AGENTS.md` e o README do produto.
- [ ] Ao receber o requisito do envelope, registrá-lo na spec, em
  `DECISIONS.md` e em novas tasks antes de alterar a implementação.