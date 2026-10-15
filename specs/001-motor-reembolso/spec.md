# Spec — Motor de Cálculo de Reembolso

**Versão:** 0.1 · **Status:** rascunho — decisões pendentes · **Última alteração:** 2026-10-15

> **Regra de ouro deste arquivo:** ele descreve o QUÊ e o PORQUÊ. Nenhuma linha
> aqui pode citar linguagem, biblioteca, classe, função ou estrutura de pasta.
> Se apareceu solução, o lugar dela é o `plan.md`.
>
> **Teste de aceitação da própria spec:** uma pessoa que nunca viu o projeto
> consegue, lendo só este arquivo, verificar se o sistema está correto?

---

## 1. Problema

O processo atual de reembolso é manual: o financeiro confere cada despesa contra
a política e devolve aprovações e recusas. O processo consome tempo e pode
produzir decisões inconsistentes ou incorretas.

## 2. Objetivo

Permitir que um conjunto de despesas de um colaborador em um período seja
avaliado de forma consistente, com o valor reembolsável e a justificativa de
cada decisão registrados em uma saída estruturada.

## 3. Fora de escopo

<Lista explícita. Este bloco vale ponto: ele impede o agente de inventar feature
e impede você de mover a trave depois.>

- Não executa pagamentos nem integra com sistemas bancários.
- Não substitui o processo de aprovação ou revisão do financeiro.
- Não oferece interface gráfica, autenticação ou gestão de usuários.
- Não permite editar a política por uma interface; a política aplicável é a
	descrita nesta spec.

## 4. Entrada e saída

**Entrada:** JSON no formato demonstrado em `exemplos/despesas-exemplo.json`.
O exemplo contém os campos abaixo; obrigatoriedade, validação e tratamento de
valores inválidos ainda precisam ser confirmados.

| Campo | Tipo | Significado | Obrigatório |
|---|---|---|---|
| `colaborador.id` | string | Identificador do colaborador | Pendente |
| `colaborador.nome` | string | Nome do colaborador | Pendente |
| `colaborador.centro_custo` | string | Centro de custo | Pendente |
| `periodo.competencia` | string `AAAA-MM` | Competência informada | Pendente |
| `periodo.inicio` | data `AAAA-MM-DD` | Início do período informado | Pendente |
| `periodo.fim` | data `AAAA-MM-DD` | Fim do período informado | Pendente |
| `despesas` | lista de objetos | Despesas a avaliar | Pendente |
| `despesas[].id` | string | Identificador da despesa | Pendente |
| `despesas[].data` | data `AAAA-MM-DD` | Data da despesa | Pendente |
| `despesas[].categoria` | string | Categoria declarada | Pendente |
| `despesas[].descricao` | string | Descrição declarada | Pendente |
| `despesas[].fornecedor` | string | Fornecedor declarado | Pendente |
| `despesas[].valor` | número | Valor informado em reais; o exemplo inclui valores negativos e mais de duas casas decimais | Pendente |
| `despesas[].tem_nota_fiscal` | booleano | Indica se foi informada nota fiscal | Pendente |

**Saída:** deve ser JSON. A estrutura e os campos ainda serão definidos; a
política exige que o resultado permita identificar o valor reembolsável e a
justificativa de cada decisão.

| Campo | Tipo | Significado |
|---|---|---|
| Pendente | Pendente | Pendente |

Um exemplo completo de saída será incluído após a definição do schema.

## 5. Regras de negócio

Cada regra recebe um ID (`RN-001`, ...). As tasks vão referenciar esses IDs.

### RN-001 — Limites-base por categoria

**Regra:** a política informa limites de R$ 60 para alimentação por dia, R$ 80
para transporte urbano por dia e R$ 250 para hospedagem por diária.
**Origem:** política do RH, itens 1–3.
**Aceite:** os limites aplicáveis devem ser verificáveis por categoria e unidade
de aplicação, a definir nas decisões AMB-001 e AMB-008.

### RN-002 — Despesas acima do limite

**Regra:** despesas acima do limite são reembolsadas parcialmente; o significado
operacional de “parcialmente” está pendente (AMB-002).
**Origem:** política do RH, item 4.
**Aceite:** pendente da decisão AMB-002.

### RN-003 — Nota fiscal

**Regra:** a política exige nota fiscal para despesas acima de R$ 100; a
fronteira e a consequência da ausência estão pendentes (AMB-003).
**Origem:** política do RH, item 5.
**Aceite:** pendente da decisão AMB-003.

### RN-004 — Colaborador em viagem

**Regra:** a política amplia limites em 50% para colaborador em viagem; a
identificação de viagem não está definida no formato de entrada (AMB-004).
**Origem:** política do RH, item 6.
**Aceite:** pendente da decisão AMB-004.

### RN-005 — Período de competência

**Regra:** despesas devem ser lançadas dentro do período de competência; a
interpretação de “lançadas” e a relação com as datas presentes na entrada estão
pendentes (AMB-005).
**Origem:** política do RH, item 7.
**Aceite:** pendente da decisão AMB-005.

### RN-006 — Duplicatas

**Regra:** duplicatas devem ser tratadas; a identificação e o tratamento estão
pendentes (AMB-006).
**Origem:** política do RH, item 8.
**Aceite:** pendente da decisão AMB-006.

### RN-007 — Categorias fora da política

**Regra:** despesas de categorias fora da política não são reembolsáveis. A
normalização e a apresentação dessa decisão na saída estão pendentes (AMB-007).
**Origem:** política do RH, item 9.
**Aceite:** uma despesa de categoria não contemplada não aumenta o total
reembolsável; a justificativa a apresentar será definida no schema de saída.

### RN-008 — Interface de cálculo

**Regra:** a aplicação recebe um arquivo JSON por meio do comando
`<comando> calcular --input despesas.json --output resultado.json` e grava um
resultado JSON no caminho indicado.
**Origem:** interface fixa do desafio.
**Aceite:** a execução com os caminhos de entrada e saída informados produz um
arquivo JSON legível; detalhes de erro e sobrescrita estão pendentes.

---

## 6. Ambiguidades identificadas e decisões

> **Esta seção é o coração da spec e vale a maior parte dos 25 pontos do critério 1.**
> Uma ambiguidade que você resolveu no código sem registrar aqui conta como
> não resolvida.

### AMB-001 — Unidade dos limites diários

**Texto original do RH:** “Alimentação tem limite de R$ 60 por dia” e
“Transporte urbano tem limite de R$ 80 por dia”.
**O que não está claro:** se o limite se aplica a cada despesa individual ou à
soma das despesas da mesma categoria na mesma data.
**Decisão:** pendente; ver `pendencias.MD`.
**Justificativa:** pendente do responsável pelo produto.
**Regra afetada:** RN-001, RN-002.

### AMB-002 — Reembolso parcial acima do limite

**Texto original do RH:** “Despesas acima do limite são reembolsadas parcialmente.”
**O que não está claro:** se o reembolso é limitado ao teto ou se outra parte
da despesa é reembolsada, e como o cálculo se aplica quando há agregação diária.
**Decisão:** pendente; ver `pendencias.MD`.
**Justificativa:** pendente do responsável pelo produto.
**Regra afetada:** RN-001, RN-002.

### AMB-003 — Fronteira e efeito da nota fiscal

**Texto original do RH:** “Nota fiscal é obrigatória acima de R$ 100.”
**O que não está claro:** se exatamente R$ 100 exige nota e qual decisão tomar
quando a nota exigida não foi informada.
**Decisão:** pendente; ver `pendencias.MD`.
**Justificativa:** pendente do responsável pelo produto.
**Regra afetada:** RN-003.

### AMB-004 — Identificação de viagem

**Texto original do RH:** “Colaborador em viagem tem limites ampliados em 50%.”
**O que não está claro:** como identificar viagem, pois não há campo explícito
para isso no exemplo de entrada.
**Decisão:** pendente; ver `pendencias.MD`.
**Justificativa:** pendente do responsável pelo produto.
**Regra afetada:** RN-004.

### AMB-005 — Período de competência e data da despesa

**Texto original do RH:** “Despesas devem ser lançadas dentro do período de competência.”
**O que não está claro:** se a validação usa `data`, `competencia`, `inicio` e
`fim`; se as pontas do período são inclusivas; e como tratar uma despesa
incorrida em um mês e apresentada em outro.
**Decisão:** pendente; ver `pendencias.MD`.
**Justificativa:** pendente do responsável pelo produto.
**Regra afetada:** RN-005.

### AMB-006 — Identificação e tratamento de duplicatas

**Texto original do RH:** “Duplicatas devem ser tratadas.”
**O que não está claro:** quais atributos definem duplicata e se uma ocorrência
repetida deve ser removida, recusada ou tratada de outra forma.
**Decisão:** pendente; ver `pendencias.MD`.
**Justificativa:** pendente do responsável pelo produto.
**Regra afetada:** RN-006.

### AMB-007 — Categorias e representação dos valores

**Texto original do RH:** “Categorias fora da política não são reembolsáveis.”
**O que não está claro:** como tratar diferenças de maiúsculas/minúsculas ou
espaços, e qual resultado/justificativa deve ser apresentado. O exemplo contém
`coworking` e `ALIMENTACAO`.
**Decisão:** pendente; ver `pendencias.MD`.
**Justificativa:** pendente do responsável pelo produto.
**Regra afetada:** RN-007.

### AMB-008 — Diária de hospedagem

**Texto original do RH:** “Hospedagem tem limite de R$ 250 por diária.”
**O que não está claro:** como obter o número de diárias; a entrada tem apenas
uma data e uma descrição textual, embora o exemplo mencione estadias de duas e
três diárias.
**Decisão:** pendente; ver `pendencias.MD`.
**Justificativa:** pendente do responsável pelo produto.
**Regra afetada:** RN-001, RN-002.

### AMB-009 — Valores negativos e estornos

**Texto original do RH:** a política não define valores negativos ou estornos.
**O que não está claro:** se o valor negativo do exemplo é ignorado, deduzido,
recusado ou tratado como outro tipo de lançamento.
**Decisão:** pendente; ver `pendencias.MD`.
**Justificativa:** pendente do responsável pelo produto.
**Regra afetada:** RN-005 e contrato de entrada/saída.

### AMB-010 — Precisão e arredondamento monetário

**Texto original do RH:** a política não especifica precisão nem arredondamento.
**O que não está claro:** como tratar valores com mais de duas casas decimais e
em qual etapa arredondar os cálculos.
**Decisão:** pendente; ver `pendencias.MD`.
**Justificativa:** pendente do responsável pelo produto.
**Regra afetada:** RN-001, RN-002 e schema de saída.

<A política tem no mínimo oito. Se você achou menos, releia
`exemplos/despesas-exemplo.json` — cada item daquele arquivo existe por um motivo.>

---

## 7. Casos de borda

| Caso | Entrada | Comportamento esperado | Regra |
|---|---|---|---|
| Mais de uma despesa da mesma categoria e data | d-001 e d-002 em 2026-07-03 | Pendente: unidade do limite diário (AMB-001) | RN-001 |
| Despesa com valor no entorno de R$ 100 sem nota | d-003 e d-004 | Pendente: fronteira e efeito da nota (AMB-003) | RN-003 |
| Categoria fora da política | d-005 (`coworking`) | Não reembolsável; justificativa e normalização pendentes | RN-007 |
| Lançamentos com mesmo fornecedor, descrição, data e valor | d-006 e d-007 | Pendente: definição de duplicata (AMB-006) | RN-006 |
| Data fora do mês indicado em competência | d-008 | Pendente: regra de competência (AMB-005) | RN-005 |
| Valor negativo | d-009 | Pendente: tratamento de estorno (AMB-009) | RN-005 |
| Hospedagem com várias diárias em texto | d-010 e d-013 | Pendente: quantidade de diárias e nota fiscal (AMB-003, AMB-008) | RN-001, RN-003 |
| Valor com mais de duas casas decimais | d-011 | Pendente: precisão e arredondamento (AMB-010) | RN-001 |
| Despesa em sábado | d-012 | A política não declara restrição por dia da semana; confirmar se não há regra adicional | RN-001 |
| Categoria com caixa diferente | d-014 (`ALIMENTACAO`) | Pendente: normalização de categoria (AMB-007) | RN-007 |

## 8. Ordem de aplicação das regras

Pendente. A ordem entre elegibilidade por categoria/período, nota fiscal,
duplicidade e limite diário precisa ser definida após as decisões em
`pendencias.MD`.

## 9. Critérios de aceite

O sistema está pronto quando:

- [ ] A CLI aceita o formato de entrada demonstrado em
	`exemplos/despesas-exemplo.json` e grava JSON no caminho solicitado.
- [ ] A saída identifica cada despesa avaliada, seu valor reembolsável e a
	justificativa da decisão; schema detalhado pendente.
- [ ] Cada regra de negócio definida tem critério de aceite numérico e teste
	automatizado correspondente.
- [ ] As decisões sobre todas as ambiguidades desta spec estão registradas e
	refletem o comportamento observado nos testes.
- [ ] O README do produto descreve como executar e testar a aplicação.

## 10. O que fica em aberto

As decisões listadas em `pendencias.MD` ainda não foram tomadas. Esta versão não
deve ser considerada especificação pronta para implementação das regras de
negócio. Quando uma decisão alterar este documento, registre a mudança em
`DECISIONS.md` antes de implementar.
