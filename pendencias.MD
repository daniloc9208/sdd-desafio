# Pendências do Produto

Este arquivo reúne decisões e informações que dependem do responsável pelo
produto. Responda cada item; depois, as decisões de negócio devem ser
registradas na spec e no `DECISIONS.md` antes de orientar implementação.

## Decisões de negócio

- [X] **AMB-001 — Limite diário:** o teto de alimentação/transporte vale por
  despesa ou pela soma da mesma categoria no dia? Se a soma ultrapassar o teto,
  como distribuir o valor reembolsável entre os itens?
  Resposta: O teto é válido por refeição (Café da manhã, almoço e jantar) sendo limitado por despesa. Caso qualquer uma delas ultrapasse, será reembolsado o teto.
  Transporte é por trecho, seguindo a mesma lógica.
  Justificativa: Decisão tomada por lógica de negócio.
- [X] **AMB-002 — Reembolso parcial:** acima do limite, reembolsa-se até o teto
  e corta-se o excedente, ou se aplica outra interpretação? Como se aplica
  quando o limite diário é compartilhado?
  Resposta: acima do limite, reembolsa-se até o teto e corta-se o excedente. O limite é por colaborador.
  Justificativa: Experiência de reembolsos anteriores.
- [X] **AMB-003 — Nota fiscal:** despesa exatamente igual a R$ 100 exige nota?
  O que ocorre quando a nota exigida não existe: recusa integral, parcial ou
  outro tratamento?
  Resposta: Notas fiscais são exigidas quando >= 100. Se a nota não existe a despesa é recusada.
  Justificativa: Decisão tomada por lógica de negócio.
- [X] **AMB-004 — Viagem:** como se identifica que o colaborador está em viagem,
  já que esse dado não aparece no JSON de exemplo? Qual o alcance temporal da
  condição de viagem?
  Resposta: Uma despesa válida de categoria `hospedagem` no lote indica viagem. Para as demais categorias, o dia seguinte à data da hospedagem recebe o limite ampliado em 50%; despesas de outras datas no lote ficam para conferência manual. Sem hospedagem válida no lote, as despesas são tratadas como normais. Todas as despesas da viagem devem ser lançadas juntas.
- [X] **AMB-005 — Competência:** a despesa é elegível pela data da despesa, pela
  data de lançamento ou por outra data? Como `competencia`, `inicio` e `fim` se
  relacionam? As datas de início e fim são inclusivas?
  Resposta: Comparar a data da despesa com a data local do cálculo. Se a diferença for maior que 90 dias, recusar; exatamente 90 dias ainda é elegível. Despesa com data futura é recusada.
- [X] **AMB-006 — Duplicatas:** quais campos tornam duas despesas duplicatas?
  Qual ocorrência deve prevalecer e como as demais devem aparecer no resultado?
  Resposta: Categoria normalizada, data, valor, descrição e fornecedor iguais definem duplicata. Manter a primeira ocorrência e recusar as posteriores. O formato atual não contém anexo, então ele não entra na comparação.
- [X] **AMB-007 — Categorias:** nomes de categoria ignoram caixa e espaços? Como
  a decisão de categoria fora da política deve ser explicada?
  Resposta: Remover espaços externos e converter para minúsculas antes da comparação. Categorias não reconhecidas são recusadas com uma justificativa que informa que estão fora da política.
- [X] **AMB-008 — Hospedagem:** como determinar o número de diárias? A entrada
  deve ganhar um campo para isso ou será adotada outra regra explícita?
  Resposta: Não inferir a quantidade de diárias a partir da descrição. Como o formato de entrada não pode ser alterado, despesas de hospedagem ficam para conferência manual e não recebem valor aprovado automaticamente.
- [X] **AMB-009 — Valores negativos/estornos:** o que significa o valor negativo
  do exemplo e como ele afeta o reembolso?
  Resposta: Valores negativos são recusados neste fluxo. Estornos não fazem parte da plataforma de reembolso e devem ser tratados em outro fluxo. A recusa é por despesa e não impede avaliar as demais despesas do lote.
- [X] **AMB-010 — Precisão monetária:** como arredondar valores com mais de duas
  casas decimais e em qual etapa do cálculo?
  Resposta: Manter precisão decimal durante o cálculo; arredondar cada valor reembolsável apresentado para duas casas decimais, usando o terceiro algarismo (0–4 para baixo; 5–9 para cima). Somar os valores por despesa já arredondados para formar os totais.
- [X] **Caso de sábado:** a política não especifica restrições por dia da semana.
  A despesa de sábado segue as mesmas regras dos demais dias?
  Resposta: Sim
- [X] **Ordem de aplicação:** erro estrutural interrompe o lote; por despesa, validar valor/data futura, normalizar e validar categoria, detectar duplicata, aplicar prazo de 90 dias, exigir nota fiscal, determinar revisão manual/viagem, aplicar limite e arredondar. A primeira regra impeditiva define o status principal.

## Contratos e validação

- [X] **Schema de saída:** JSON com versão, data do cálculo, moeda BRL, colaborador, período, uma decisão por despesa, status, valores e motivos; total aprovado automaticamente e total em revisão manual. Valores monetários na saída são strings com duas casas decimais.
- [X] **Validação de entrada:** todos os campos do exemplo são obrigatórios e validados por tipo/formato; datas devem existir no calendário e `periodo.inicio <= periodo.fim`; IDs são únicos. Campo ausente, tipo/formato incorreto, JSON inválido ou ID repetido interrompe o lote sem resultado parcial. Valor zero, negativo ou data futura recusa somente a despesa correspondente.
- [X] **Arquivo de saída e erros:** substituir arquivo existente somente após cálculo bem-sucedido. Erro de entrada/leitura/gravação retorna código diferente de zero e preserva saída anterior; resultado concluído retorna zero mesmo com recusas ou revisões manuais.

## Furos identificados e resolvidos na spec

Os itens abaixo foram identificados durante revisão funcional da spec v0.2. As
respostas foram incorporadas às versões v0.3 e v0.4 e registradas em
`DECISIONS.md`.

- [X] **FURO-001 — Hospedagem recusada ainda ativa indício de viagem?**
  A RN-004 diz que uma hospedagem com data válida e valor positivo ativa o indício de viagem "mesmo que depois seja recusada por prazo ou falta de nota fiscal". A ordem de aplicação (Seção 8) aplica nota fiscal (passo 6) antes de determinar viagem (passo 7). Quando o passo 7 avalia se existe hospedagem no lote, uma hospedagem já recusada no passo 6 conta como indício de viagem?
  **Impacto:** define se d-013 (recusada por falta de nota) ativa o indício de viagem para as demais despesas do lote — e portanto se d-014 vai para `revisao_manual` ou é tratada normalmente.
  Resposta: deve ser tratada novamente. A despesa não está válida para reembolso, mas não deixou de ser uma viagem

- [X] **FURO-002 — Múltiplas hospedagens no mesmo lote: qual data-base usar para o dia de viagem?**
  O arquivo de exemplo tem d-010 (`2026-07-14`) e d-013 (`2026-07-22`), ambas de `hospedagem`. A RN-004 fala em singular ("o dia seguinte à data do lançamento de hospedagem"). Com duas hospedagens, cada uma gera seu próprio "dia seguinte" com limite ampliado, ou apenas a primeira (ou última) hospedagem é usada como referência?
  **Impacto:** define o comportamento de d-012 (`2026-07-18`) e de qualquer despesa em `2026-07-23` — se estariam em `revisao_manual` ou receberiam limite ampliado.
  Resposta:Ambas hospedagens geram automaticamente os limites ampliados. As demais serão necessárias passar por validação manual.

- [X] **FURO-003 — Múltiplas despesas elegíveis no mesmo dia seguinte à hospedagem recebem cada uma o teto ampliado individualmente?**
  A AMB-001 definiu que o limite é por despesa. Confirmar que essa lógica se mantém no contexto de viagem: se houver duas refeições e um transporte no dia seguinte à hospedagem, cada despesa recebe seu próprio teto ampliado (alimentação R$ 90, transporte R$ 120) individualmente — sem agregação diária mesmo em contexto de viagem.
  Resposta: Sim, deverão ter o teto ampliado.

- [X] **FURO-005 — Uma despesa pode ter mais de um código em `motivos`?**
  A Seção 8 diz "a primeira regra impeditiva define o status principal", mas `motivos` é uma lista. A spec não define se múltiplos motivos podem coexistir na saída para uma mesma despesa. Exemplos: despesa `reembolsada_parcialmente` num contexto de viagem — terá `limite_aplicado` e `limite_viagem_aplicado` juntos, ou apenas um?
  **Impacto:** contrato de saída e comportamento esperado nos testes.
  Resposta: Sim, os motivos devem ser cumulativos e explicam as tratativas tomadas para a despesa.

- [X] **FURO-006 — O código `dentro_do_limite` é emitido obrigatoriamente para despesas com status `reembolsada`?**
  O código `dentro_do_limite` consta na lista de códigos possíveis (Seção 4), mas nenhuma RN descreve quando deve ser emitido. O campo `motivos` é obrigatório e não vazio para toda despesa? Uma despesa de R$ 45 de alimentação, no prazo, sem duplicata, com nota — o que vai em `motivos`?
  Resposta: É obrigatório e não vazio. Deve se conter pelo menos um concluído ou algo relacionado.

- [X] **FURO-010 — Quando usar `revisao_manual_viagem` vs. `revisao_manual_hospedagem`?**
  Dois códigos de revisão manual existem na lista da Seção 4, mas a spec não declara explicitamente qual se aplica a cada situação. Confirmar: `revisao_manual_hospedagem` é para despesas da categoria `hospedagem`; `revisao_manual_viagem` é para despesas de outras categorias em datas não determinadas como dia de viagem?
  Resposta: Apenas manter o revisão manual Viagem, o status está ambiguo.

- [X] **FURO-007 — `periodo.inicio > periodo.fim` é erro estrutural que interrompe o lote?**
  A Seção 8, passo 1, lista como interruptores "campo ausente, tipo/formato inválido ou ID repetido". A restrição `inicio <= fim` é semântica, não de formato. Confirmar se ela também interrompe o lote sem resultado parcial.
  Resposta: Sim, interrompe o lote pois é uma validação.

- [X] **FURO-008 — O sistema valida se `periodo.inicio`/`periodo.fim` pertencem ao mês da `competencia`?**
  A spec não define se um lote com `competencia: "2026-07"` e `inicio: "2026-01-01"` é aceito ou recusado. Confirmar se há validação de coerência entre competência e intervalo, ou se o período é metadado livre.
  Resposta: Não necessariamente. O periodo inicial deve ser iniciado na competência, mas o final não é necessariamente obrigatório estar nop mesmo mes.

- [X] **FURO-009 — Saída com lista de despesas vazia: como ficam os totais e a lista?**
  A spec permite `despesas` vazia na entrada, mas não especifica a saída nesse caso. Confirmar: `totais.valor_reembolsavel` e `totais.valor_em_revisao` devem ser `"0.00"`, e `despesas` na saída deve ser `[]`.
  Resposta: `totais.valor_reembolsavel` e `totais.valor_em_revisao` devem ser `"0.00"`, e `despesas` na saída deve ser `[]`.

- [X] **FURO-011 — Qual é o valor normativo de `versao_schema` na saída?**
  O exemplo mostra `"1.0"`, mas a spec não declara esse valor como normativo nem define quando ele muda. Confirmar que `"1.0"` é o valor fixo para esta versão da spec.
  Resposta: É o valor fixo.

- [X] **FURO-012 — Como tratar valor positivo que arredonda para R$ 0,00?**
  Resposta: Recusar a despesa com motivo `valor_inferior_ao_centavo`. R$ 0,005 arredonda para R$ 0,01 e não cai nesta recusa.

- [X] **FURO-013 — Continuar avaliando regras do item após uma recusa?**
  Resposta: Não. A primeira regra de recusa encerra a avaliação daquele item; seus motivos anteriores são preservados, o motivo da recusa é acrescentado e as demais despesas do lote continuam sendo processadas.

- [X] **FURO-014 — Como comparar valores na identificação de duplicatas?**
  Resposta: Comparar valores decimais numericamente antes do arredondamento de apresentação. `54.90` e `54.9` são iguais; `33.331` e `33.334` são diferentes.

- [X] **FURO-015 — Como tratar propriedades não previstas no JSON de entrada?**
  Resposta: Rejeitar propriedades extras em qualquer nível como erro estrutural, sem saída parcial.

- [X] **FURO-016 — O que fazer se entrada e saída apontarem para o mesmo arquivo?**
  Resposta: Rejeitar a execução antes de gravar e preservar o arquivo de entrada.

- [X] **FURO-017 — Qual data usar se a execução atravessar a meia-noite?**
  Resposta: Capturar a data local uma vez no início da execução, usá-la para todo o lote e registrá-la em `data_calculo`.

### Consolidação aplicada

- Toda despesa de hospedagem com categoria reconhecida, data válida e valor
  positivo gera o dia seguinte como data de viagem, mesmo se for recusada depois
  por duplicidade, prazo ou ausência de nota. Cada data de hospedagem gera seu
  próprio dia seguinte; datas coincidentes não acumulam aumentos acima de 50%.
- Cada despesa de alimentação ou transporte em uma data de viagem recebe seu
  próprio teto ampliado. Despesas elegíveis de outras datas, e hospedagens cuja
  quantidade de diárias não é conhecida, ficam em revisão manual.
- O status de revisão é `revisao_manual`; o único código de motivo de revisão é
  `revisao_manual_viagem`. A descrição do motivo explica a causa específica.
- `motivos` é obrigatório, nunca vazio e cumulativo para as regras efetivamente
  aplicadas. Lista vazia de despesas produz `[]` e totais `"0.00"`.
- `periodo.inicio` deve pertencer ao mês/ano de `periodo.competencia`; `fim` pode
  ultrapassar esse mês, desde que seja igual ou posterior ao início.
- `versao_schema` tem valor fixo `"1.0"` para este contrato.

## Execução e entrega

- [X] **Linguagem:** Python, escolha confirmada em 2026-10-16.
- [X] **Plano técnico:** Python 3.11+, pacote `src/reembolso`, entry point
  `reembolso`, `argparse`/`json`/`decimal`, pytest, Ruff, núcleo puro e política
  centralizada registrados em `specs/001-motor-reembolso/plan.md`.
- [ ] Atualizar o README do produto com instalação, execução, testes e lint/format.
- [ ] Ao receber o requisito do envelope, registrá-lo na spec, em
  `DECISIONS.md` e em novas tasks antes de alterar a implementação.
