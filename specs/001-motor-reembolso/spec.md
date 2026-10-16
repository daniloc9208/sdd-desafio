# Spec — Motor de Cálculo de Reembolso

**Versão:** 0.4 · **Status:** rascunho para validação · **Última alteração:** 2026-10-16

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

- Não executa pagamentos nem integra com sistemas bancários.
- Não substitui o processo de aprovação ou revisão do financeiro.
- Não oferece interface gráfica, autenticação ou gestão de usuários.
- Não permite editar a política por uma interface; a política aplicável é a
	descrita nesta spec.
- Não calcula nem compensa estornos; valores negativos são recusados neste fluxo.
- Não determina automaticamente a quantidade de diárias de hospedagem nem
  conclui despesas que dependam de conferência manual.

## 4. Entrada e saída

**Entrada:** JSON no formato demonstrado em `exemplos/despesas-exemplo.json`.
Todos os campos presentes nesse formato são obrigatórios e devem ter os tipos e
formatos abaixo.

| Campo | Tipo | Significado | Obrigatório |
|---|---|---|---|
| `colaborador.id` | string não vazia após remover espaços externos | Identificador do colaborador | Sim |
| `colaborador.nome` | string não vazia após remover espaços externos | Nome do colaborador | Sim |
| `colaborador.centro_custo` | string não vazia após remover espaços externos | Centro de custo | Sim |
| `periodo.competencia` | string `AAAA-MM`, mês entre `01` e `12` | Competência do lote | Sim |
| `periodo.inicio` | data válida `AAAA-MM-DD` cujo ano e mês correspondam a `competencia` | Início informado para o lote | Sim |
| `periodo.fim` | data válida `AAAA-MM-DD`, igual ou posterior a `inicio` | Fim informado para o lote; pode estar em mês posterior à competência | Sim |
| `despesas` | lista de objetos | Despesas a avaliar; pode ser vazia | Sim |
| `despesas[].id` | string não vazia após remover espaços externos e única no lote após essa remoção | Identificador da despesa | Sim |
| `despesas[].data` | data válida `AAAA-MM-DD` | Data em que a despesa ocorreu | Sim |
| `despesas[].categoria` | string não vazia após remover espaços externos | Categoria declarada | Sim |
| `despesas[].descricao` | string não vazia após remover espaços externos | Descrição declarada | Sim |
| `despesas[].fornecedor` | string não vazia após remover espaços externos | Fornecedor declarado | Sim |
| `despesas[].valor` | número decimal finito | Valor em reais; pode ter mais de duas casas e, após arredondamento monetário, deve resultar em pelo menos R$ 0,01 para ser reembolsável | Sim |
| `despesas[].tem_nota_fiscal` | booleano | Indica se foi informada nota fiscal | Sim |

O documento, `colaborador`, `periodo` e cada item de `despesas` devem conter
somente os campos definidos nesta tabela. Propriedade adicional em qualquer
um desses níveis é erro estrutural e interrompe o lote.

**Saída:** JSON UTF-8 gravado no caminho indicado. Valores monetários são
representados como strings decimais com duas casas e moeda `BRL`.

| Campo | Tipo | Significado |
|---|---|---|
| `versao_schema` | string | Sempre `1.0` para este contrato |
| `data_calculo` | data `AAAA-MM-DD` | Data local capturada no início da execução; referência única da regra de 90 dias para todo o lote |
| `moeda` | string | Sempre `BRL` |
| `colaborador` | objeto | Identificação do colaborador recebida na entrada |
| `periodo` | objeto | Competência e intervalo recebidos na entrada |
| `despesas` | lista | Um resultado por despesa, preservando a ordem de entrada |
| `despesas[].id` | string | Identificador original da despesa |
| `despesas[].status` | string | `reembolsada`, `reembolsada_parcialmente`, `recusada` ou `revisao_manual`; revisão não é aprovação |
| `despesas[].valor_informado` | string decimal | Valor original da despesa em BRL, com duas casas após arredondamento |
| `despesas[].valor_reembolsavel` | string decimal | Valor aprovado automaticamente; zero para despesa recusada ou em revisão manual |
| `despesas[].motivos` | lista de objetos | Códigos estáveis e descrições legíveis que explicam o status e os ajustes |
| `despesas[].motivos[].codigo` | string | Código estável do motivo |
| `despesas[].motivos[].descricao` | string | Explicação em português para a pessoa usuária |
| `totais.valor_reembolsavel` | string decimal | Soma dos valores aprovados automaticamente; estornos não são processados neste fluxo |
| `totais.valor_em_revisao` | string decimal | Soma dos valores informados das despesas em conferência manual; não integra o reembolso aprovado |

Os valores de `status` são definidos assim: `reembolsada` quando todo o valor
elegível é aprovado, `reembolsada_parcialmente` quando o teto reduz o valor,
`recusada` quando uma regra impeditiva se aplica e `revisao_manual` quando falta
informação para decidir sem análise humana. O campo `motivos` é obrigatório e
nunca pode ser vazio. Deve conter todos os códigos das regras e tratativas
efetivamente aplicadas à despesa, na ordem em que foram aplicadas; quando não há
outra tratativa, usar `dentro_do_limite` para registrar a aprovação. A primeira
regra impeditiva determina o status, mas não apaga motivos anteriores já
aplicados. Ao encontrar uma regra de recusa, encerrar a avaliação daquela
despesa, preservar os motivos já registrados e acrescentar o motivo da recusa;
continuar avaliando as demais despesas do lote. Códigos possíveis em
`motivos[].codigo`:
`valor_zero_invalido`, `valor_negativo_fora_escopo`, `valor_inferior_ao_centavo`, `data_futura`,
`categoria_fora_politica`, `duplicata`, `prazo_excedido`,
`nota_fiscal_ausente`, `revisao_manual_viagem`, `limite_aplicado`,
`limite_viagem_aplicado` e `dentro_do_limite`. Para qualquer revisão manual,
usar o único código `revisao_manual_viagem`; a descrição deve dizer se a causa é
diária de hospedagem indeterminável ou data não identificável como dia de viagem.
Uma despesa parcialmente reembolsada em viagem inclui ambos os códigos
`limite_viagem_aplicado` e `limite_aplicado`. Uma despesa aprovada abaixo do
limite ampliado inclui `limite_viagem_aplicado` e `dentro_do_limite`.

Se `despesas` for uma lista vazia, a saída contém `despesas: []`,
`totais.valor_reembolsavel: "0.00"` e `totais.valor_em_revisao: "0.00"`.

Exemplo reduzido para um cálculo de referência em 2026-10-16:

```json
{
	"versao_schema": "1.0",
	"data_calculo": "2026-10-16",
	"moeda": "BRL",
	"colaborador": { "id": "c-0417", "nome": "Marina Volpi", "centro_custo": "CC-ENG-PLATAFORMA" },
	"periodo": { "competencia": "2026-07", "inicio": "2026-07-01", "fim": "2026-07-31" },
	"despesas": [
		{
			"id": "d-014",
			"status": "reembolsada_parcialmente",
			"valor_informado": "61.00",
			"valor_reembolsavel": "60.00",
			"motivos": [
				{ "codigo": "limite_aplicado", "descricao": "Valor limitado ao teto aplicável." }
			]
		}
	],
	"totais": { "valor_reembolsavel": "60.00", "valor_em_revisao": "0.00" }
}
```

## 5. Regras de negócio

Cada regra recebe um ID (`RN-001`, ...). As tasks vão referenciar esses IDs.

### RN-001 — Limites por despesa

**Regra:** cada colaborador tem limite de R$ 60 por despesa de alimentação
(refeição) e R$ 80 por despesa de transporte urbano (trecho). Não há soma
diária nem cota compartilhada entre despesas ou colaboradores.
**Origem:** política do RH, itens 1–2; decisão AMB-001.
**Aceite:** alimentação de R$ 72,50 pode reembolsar até R$ 60,00; transporte de
R$ 100,00 pode reembolsar até R$ 80,00, antes de eventual ampliação por viagem.

### RN-002 — Reembolso limitado ao teto

**Regra:** para despesa elegível acima do limite aplicável, reembolsar o menor
entre o valor informado e o teto; o excedente não é reembolsado.
**Origem:** política do RH, item 4; decisão AMB-002.
**Aceite:** alimentação de R$ 72,50 com teto de R$ 60,00 resulta em R$ 60,00.

### RN-003 — Nota fiscal

**Regra:** despesa com valor original maior ou igual a R$ 100,00 exige nota
fiscal. Sem nota, a despesa é recusada integralmente, mesmo que o limite
reembolsável fosse inferior a R$ 100,00.
**Origem:** política do RH, item 5; decisão AMB-003.
**Aceite:** R$ 100,00 sem nota é recusado; R$ 99,99 sem nota não é recusado por
esta regra.

### RN-004 — Identificação e limites de viagem

**Regra:** cada despesa de categoria normalizada `hospedagem`, com data válida e
valor positivo, gera como data de viagem o dia calendário seguinte. Esse indício
permanece válido mesmo que a hospedagem seja depois recusada por duplicidade,
prazo ou falta de nota fiscal. Despesas elegíveis de outras categorias cuja data
coincida com pelo menos uma dessas datas recebem limite aumentado em 50%; o
aumento é aplicado uma única vez, ainda que mais de uma hospedagem gere a mesma
data. Cada despesa tem seu próprio teto ampliado, sem soma diária. Se o lote
contiver hospedagem e uma despesa elegível não estiver em nenhuma data de viagem
identificada, ela fica em `revisao_manual`, sem receber limite normal nem
ampliado. A própria hospedagem fica em `revisao_manual`, pois a entrada não
permite determinar as diárias. Sem nenhuma hospedagem com data válida e valor
positivo, não há inferência de viagem nem revisão manual por esse motivo.
**Origem:** política do RH, item 6; decisões AMB-004 e AMB-008.
**Aceite:** hospedagens em 2026-07-14 e 2026-07-22 geram dias de viagem
2026-07-15 e 2026-07-23. Em cada dia, cada despesa de alimentação recebe teto
de R$ 90,00 e cada transporte recebe teto de R$ 120,00. Despesas elegíveis em
outras datas e as próprias hospedagens ficam em revisão manual. Uma hospedagem
recusada por nota ainda gera seu dia de viagem.

### RN-005 — Prazo para apresentação

**Regra:** capturar a data local uma única vez no início da execução e registrá-la
em `data_calculo`. Comparar todas as despesas com essa mesma data. Se a despesa
for futura ou tiver ocorrido há mais de 90 dias corridos, recusá-la. Uma despesa
exatamente 90 dias anterior à data do cálculo ainda é elegível por prazo. Os
campos de período identificam o lote; não substituem esta verificação.
**Origem:** política do RH, item 7; decisão AMB-005.
**Aceite:** no cálculo de 2026-10-15, 2026-07-17 tem 90 dias e passa pela regra;
2026-07-16 tem 91 dias e é recusada.

### RN-006 — Duplicatas

**Regra:** duas despesas com categoria normalizada, data, valor decimal
numericamente igual antes de arredondar, descrição e fornecedor iguais são
duplicatas. Portanto, `54.90` e `54.9` são valores iguais, mas `33.331` e
`33.334` são diferentes, mesmo que possam ser exibidos com os mesmos centavos.
Para descrição e fornecedor, comparar o texto exatamente como recebido.
Manter a primeira na ordem do arquivo e recusar as seguintes. O formato atual
não tem anexo, portanto anexo não participa da comparação.
**Origem:** política do RH, item 8; decisão AMB-006 e contrato atual de entrada.
**Aceite:** entre d-006 e d-007, manter d-006 e recusar d-007 como duplicata.
Valores JSON numericamente iguais, como `54.90` e `54.9`, contam como iguais;
valores distintos antes do arredondamento, como `33.331` e `33.334`, não são
duplicatas apenas por serem apresentados com os mesmos centavos.

### RN-007 — Categorias

**Regra:** comparar categoria após remover espaços externos e converter para
minúsculas. As categorias reconhecidas são `alimentacao`, `transporte_urbano` e
`hospedagem`. Categoria não reconhecida é recusada com motivo
`categoria_fora_politica`.
**Origem:** política do RH, item 9; decisão AMB-007.
**Aceite:** `ALIMENTACAO` é reconhecida como `alimentacao`; `coworking` é
recusada.

### RN-008 — Valores positivos e estornos fora de escopo

**Regra:** valor zero é inválido, valor negativo é recusado como não elegível
neste fluxo e valor positivo que, arredondado para duas casas, resulte em
R$ 0,00 é recusado por ser inferior a um centavo reembolsável. Estornos devem
ser tratados em fluxo separado; não reduzem nem aumentam o total deste cálculo.
A invalidez afeta apenas a despesa, permitindo avaliar as demais despesas
válidas do lote.
**Origem:** decisões AMB-009 e contrato validado pelo responsável do produto.
**Aceite:** d-009, de R$ -45,00, é recusada com `valor_negativo_fora_escopo`; um
valor zero é recusado com `valor_zero_invalido`; R$ 0,004 é recusado com
`valor_inferior_ao_centavo`; nenhuma dessas recusas altera o total.
R$ 0,005 arredonda para R$ 0,01 e não é recusado por ser inferior a um centavo.

### RN-009 — Precisão monetária

**Regra:** manter precisão decimal durante os cálculos e arredondar cada valor
monetário apresentado por despesa para duas casas: terceiro algarismo decimal de
0 a 4 arredonda para baixo; de 5 a 9, para cima. Os totais são a soma dos valores
por despesa já arredondados, inclusive o total em revisão manual.
**Origem:** decisão AMB-010 e contrato validado pelo responsável do produto.
**Aceite:** R$ 33,333 resulta em R$ 33,33; R$ 33,335 resulta em R$ 33,34. Os
totais conferem com a soma dos valores por despesa exibidos.

### RN-010 — Interface de cálculo

**Regra:** a aplicação recebe um arquivo JSON por meio do comando
`<comando> calcular --input despesas.json --output resultado.json` e grava um
resultado JSON no caminho indicado.
**Origem:** interface fixa do desafio.
**Aceite:** a execução com os caminhos de entrada e saída informados produz um
arquivo JSON válido segundo o contrato desta seção.

### RN-011 — Competência e intervalo do lote

**Regra:** o ano e mês de `periodo.inicio` devem corresponder a
`periodo.competencia`; o dia de início pode ser qualquer dia válido daquele mês.
`periodo.fim` deve ser igual ou posterior a `periodo.inicio`, mas pode pertencer
a um mês posterior à competência. As datas das despesas são elegíveis pelo
prazo da RN-005 e não precisam estar contidas no intervalo do lote.
**Origem:** decisão FURO-007 e FURO-008.
**Aceite:** competência `2026-07`, início `2026-07-01` e fim `2026-08-15` são
válidos; início `2026-06-30`, fim anterior ao início ou data impossível são
erros estruturais que interrompem o lote.

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
**Decisão:** aplicar o teto por despesa: alimentação por refeição e transporte
urbano por trecho. Não somar despesas do mesmo dia para aplicar o teto.
**Justificativa:** reflete a unidade de consumo informada para cada categoria e
permite avaliar cada lançamento de forma independente.
**Regra afetada:** RN-001, RN-002.

### AMB-002 — Reembolso parcial acima do limite

**Texto original do RH:** “Despesas acima do limite são reembolsadas parcialmente.”
**O que não está claro:** qual parte da despesa acima do limite é reembolsada.
**Decisão:** reembolsar somente até o teto aplicável e não reembolsar o
excedente; o limite pertence ao colaborador e é aplicado individualmente a cada
despesa conforme RN-001, sem agregação diária.
**Justificativa:** segue a experiência de reembolsos anteriores do responsável
pelo produto.
**Regra afetada:** RN-001, RN-002.

### AMB-003 — Fronteira e efeito da nota fiscal

**Texto original do RH:** “Nota fiscal é obrigatória acima de R$ 100.”
**O que não está claro:** se exatamente R$ 100 exige nota e qual decisão tomar
quando a nota exigida não foi informada.
**Decisão:** exigir nota quando o valor original for maior ou igual a R$ 100,00;
sem nota, recusar a despesa integralmente.
**Justificativa:** decisão de negócio do responsável pelo produto.
**Regra afetada:** RN-003.

### AMB-004 — Identificação de viagem

**Texto original do RH:** “Colaborador em viagem tem limites ampliados em 50%.”
**O que não está claro:** como identificar viagem e quais despesas/datas recebem
o limite ampliado, pois não há campo explícito de viagem.
**Decisão:** um lançamento de hospedagem com data válida e valor positivo no
lote é o indício de viagem, mesmo que depois seja recusado por prazo ou falta
de nota fiscal. Para despesas não relacionadas à hospedagem, a data de viagem identificável é
o dia seguinte à data do lançamento de hospedagem. Despesas em outras datas do
lote recebem `revisao_manual` para confirmação humana. Se o lote não contiver
hospedagem, as despesas são tratadas como não estando em viagem. Todos os itens
da viagem devem ser enviados juntos para que o sistema possa avaliar o lote.
**Justificativa:** a hospedagem comprova o pernoite, mas o formato de entrada
não contém datas de início/fim da viagem para inferir outras diárias.
**Regra afetada:** RN-004.

### AMB-005 — Período de competência e data da despesa

**Texto original do RH:** “Despesas devem ser lançadas dentro do período de competência.”
**O que não está claro:** qual é a data de referência e a fronteira do prazo.
**Decisão:** capturar a data local uma única vez no início do cálculo e usar a
mesma referência para todas as despesas. Recusar se a despesa for futura ou
tiver ocorrido há mais de 90 dias corridos; aceitar a fronteira de exatamente
90 dias. O período informado identifica o lote e não substitui esse prazo.
**Justificativa:** decisão do responsável pelo produto; limita o prazo para
apresentação a 90 dias da ocorrência da despesa.
**Regra afetada:** RN-005.

### AMB-006 — Identificação e tratamento de duplicatas

**Texto original do RH:** “Duplicatas devem ser tratadas.”
**O que não está claro:** quais atributos disponíveis no formato atual definem
duplicata e qual ocorrência deve prevalecer.
**Decisão:** considerar duplicadas as despesas com categoria normalizada, data,
valor decimal numericamente igual antes do arredondamento, descrição e fornecedor
idênticos. Manter a primeira na ordem do arquivo e recusar as posteriores. O
formato atual não tem campo de anexo; portanto, anexos não participam da
comparação.
**Justificativa:** usa os dados disponíveis sem alterar o formato de entrada e
preserva o primeiro lançamento recebido.
**Regra afetada:** RN-006.

### AMB-007 — Normalização de categoria e categorias não reconhecidas

**Texto original do RH:** “Categorias fora da política não são reembolsáveis.”
**O que não está claro:** como tratar diferenças de caixa/espaçamento e
categorias não reconhecidas.
**Decisão:** remover espaços externos e converter a categoria para minúsculas
antes da comparação. Categorias reconhecidas: `alimentacao`,
`transporte_urbano` e `hospedagem`. Categoria divergente é recusada e recebe
justificativa legível.
**Justificativa:** permite variação de caixa e espaços acidentais sem aceitar
categorias que não constam da política.
**Regra afetada:** RN-007.

### AMB-008 — Diária de hospedagem

**Texto original do RH:** “Hospedagem tem limite de R$ 250 por diária.”
**O que não está claro:** como obter o número de diárias; a entrada tem apenas
uma data e uma descrição textual, embora o exemplo mencione estadias de duas e
três diárias.
**Decisão:** não inferir a quantidade de diárias pela descrição. Despesas de
hospedagem ficam em `revisao_manual`, sem valor aprovado automaticamente.
**Justificativa:** o formato de entrada é fixo e não fornece um campo confiável
para quantidade de diárias.
**Regra afetada:** RN-001, RN-002.

### AMB-009 — Valores negativos e estornos

**Texto original do RH:** a política não define valores negativos ou estornos.
**O que não está claro:** como o fluxo de reembolso trata valores negativos.
**Decisão:** recusar valores negativos neste fluxo; estornos pertencem a outro
fluxo e não alteram os totais deste cálculo.
**Justificativa:** a plataforma trata reembolsos; estornos não são reembolsos e
devem ser tratados no fluxo apropriado.
**Regra afetada:** RN-008 e contrato de entrada/saída.

### AMB-010 — Precisão e arredondamento monetário

**Texto original do RH:** a política não especifica precisão nem arredondamento.
**O que não está claro:** como tratar valores com mais de duas casas decimais,
em qual etapa arredondar e o que fazer quando um valor positivo se torna zero
na apresentação em centavos.
**Decisão:** manter precisão decimal durante o cálculo, arredondar cada valor
por despesa apenas para apresentação e somar os valores apresentados para obter
os totais. Recusar valores positivos que arredondem para R$ 0,00.
**Justificativa:** mantém os totais iguais à soma dos valores apresentados e
evita aprovar uma despesa sem valor reembolsável representável em centavos.
**Regra afetada:** RN-009 e schema de saída.

---

## 7. Casos de borda

| Caso | Entrada | Comportamento esperado (data de cálculo 2026-07-31) | Regra |
|---|---|---|---|
| Despesas de alimentação no mesmo dia | d-001 e d-002 | Aplicar teto por despesa: R$ 60,00 e R$ 38,00 | RN-001 |
| Transporte sem nota a partir de R$ 100 | d-003 e d-004 | Recusar ambas por falta de nota fiscal | RN-003 |
| Categoria fora da política | d-005 (`coworking`) | Recusar com motivo `categoria_fora_politica` | RN-007 |
| Duplicatas de negócio | d-006 e d-007 | Manter d-006; recusar d-007 como duplicata | RN-006 |
| Despesa com mais de 90 dias | d-008 | Recusar por prazo; diferença de 107 dias | RN-005 |
| Valor negativo | d-009 | Recusar apenas d-009; não alterar os demais resultados | RN-008 |
| Hospedagem com diária indeterminável | d-010 | Status `revisao_manual`, motivo `revisao_manual_viagem`, valor aprovado R$ 0,00 | RN-004 |
| Café da manhã no dia seguinte à primeira hospedagem | d-011 | Teto de viagem R$ 90,00; reembolso R$ 33,33; motivos `limite_viagem_aplicado` e `dentro_do_limite` | RN-004, RN-009 |
| Despesa em sábado com hospedagens no lote | d-012 | Status `revisao_manual`, pois não ocorre no dia seguinte a nenhuma hospedagem | RN-004 |
| Categoria com caixa diferente e hospedagens no lote | d-014 (`ALIMENTACAO`) | Status `revisao_manual`, pois não ocorre no dia seguinte a nenhuma hospedagem | RN-004, RN-007 |
| Hospedagem sem nota acima de R$ 100 | d-013 | Recusar por falta de nota; ainda gera dia de viagem em 2026-07-23 | RN-003, RN-004 |
| Múltiplas hospedagens | d-010 e d-013 | Geram dias de viagem distintos: 2026-07-15 e 2026-07-23; recusa posterior de d-013 não remove o segundo dia | RN-004 |
| Dia seguinte à segunda hospedagem | Despesa elegível em 2026-07-23 | Teto individual: alimentação R$ 90,00; transporte R$ 120,00 | RN-004 |
| Duas refeições no mesmo dia de viagem | Duas despesas elegíveis de alimentação em 2026-07-15 | Cada despesa pode reembolsar até R$ 90,00; não há agregação diária | RN-001, RN-004 |
| Limite parcial em viagem | Despesa de alimentação de R$ 100,00 em 2026-07-15, com nota | Reembolso R$ 90,00; status parcial; motivos `limite_viagem_aplicado` e `limite_aplicado` | RN-002, RN-004 |
| Lista de despesas vazia | `despesas: []` | Saída com lista vazia e ambos totais em `"0.00"` | Contrato de saída |
| Competência e início coerentes | `competencia: "2026-07"`, início `2026-07-01`, fim `2026-08-15` | Lote aceito | RN-011 |
| Início em competência diferente | `competencia: "2026-07"`, início `2026-06-30` | Lote rejeitado sem resultado | RN-011 |
| Versão do schema | Qualquer lote estruturalmente válido | `versao_schema` é exatamente `"1.0"` | Contrato de saída |
| Valor positivo abaixo de meio centavo | Despesa de R$ 0,004 | Recusar com `valor_inferior_ao_centavo`; valor reembolsável `"0.00"` | RN-008, RN-009 |
| Valor no meio centavo | Despesa de R$ 0,005 | Arredondar para R$ 0,01; não recusar por valor subcentavo | RN-008, RN-009 |
| Igualdade de valor para duplicidade | Valores `54.90` e `54.9` em despesas com os demais campos-chave iguais | Tratar como duplicatas | RN-006 |
| Valores distintos que exibem os mesmos centavos | `33.331` e `33.334` em despesas com os demais campos-chave iguais | Não tratar como duplicatas por valor | RN-006, RN-009 |
| Propriedade JSON desconhecida | Campo adicional em qualquer objeto da entrada | Interromper o lote sem saída parcial | Contrato de entrada |
| Entrada e saída no mesmo arquivo | `--input` e `--output` referem-se ao mesmo arquivo | Interromper sem alterar o arquivo de entrada | RN-010 |

## 8. Ordem de aplicação das regras

As regras são aplicadas nesta ordem. A primeira regra impeditiva define o status
principal da despesa; a saída registra o motivo correspondente. A ordem da lista
é normativa:

1. Capturar a data local uma única vez para o lote e registrá-la como
	`data_calculo`. Validar o documento JSON, os campos obrigatórios e a ausência
	de propriedades não especificadas. Erro estrutural, campo ausente,
	tipo/formato inválido, ID repetido após remoção de espaços externos, início
	fora da competência ou fim anterior ao início interrompe o lote. Se os
	caminhos de entrada e saída apontarem para o mesmo arquivo, interromper sem
	gravar. Em qualquer erro, não gerar resultado parcial nem alterar arquivos.
2. Para todas as despesas estruturalmente válidas, normalizar a categoria e
	identificar as datas de hospedagem que geram viagem: cada item com categoria
	`hospedagem`, data válida e valor positivo gera o dia calendário seguinte,
	mesmo que depois seja recusado por duplicidade, prazo ou falta de nota.
	Datas repetidas geram um único dia de viagem; o aumento de limite não acumula.
3. Para cada despesa, recusar valor zero, valor negativo, data futura ou valor
	positivo que arredondado para duas casas resulte em R$ 0,00. Essas recusas
	são por item e não impedem a avaliação das demais despesas válidas.
4. Validar a categoria normalizada; recusar categoria não reconhecida.
5. Detectar duplicatas entre despesas não recusadas pelos passos anteriores,
	preservando a primeira na ordem de entrada e recusando as posteriores.
6. Recusar despesa ocorrida há mais de 90 dias, comparando com a data local do
	cálculo. Exatamente 90 dias é elegível.
7. Exigir nota fiscal para valor original maior ou igual a R$ 100,00; sem nota,
	recusar a despesa integralmente.
	Ao encontrar uma recusa nos passos 3–7, encerrar o processamento daquela
	despesa, preservar os motivos já registrados e acrescentar o motivo da
	recusa. Continuar o processamento dos outros itens do lote.
8. Para despesa não recusada, se a categoria for `hospedagem`, definir status
	`revisao_manual` e motivo `revisao_manual_viagem`, pois as diárias não podem
	ser determinadas. Se houver hospedagem no lote e a data da despesa não for
	uma data de viagem identificada, definir o mesmo status e motivo para itens
	elegíveis de outras categorias. A descrição do motivo distingue essas duas
	causas. Uma recusa anterior prevalece e não é substituída por revisão manual.
9. Para as demais despesas elegíveis, aplicar o teto da categoria e, se a data
	estiver no conjunto de datas de viagem, aumentar o teto em 50%. Reembolsar
	no máximo o valor informado e registrar todos os motivos aplicáveis.
10. Arredondar cada valor monetário por despesa para duas casas e somar os
	 valores já arredondados para formar os totais.

O código de saída da CLI é zero quando um resultado JSON completo foi gerado,
mesmo que existam despesas recusadas ou em revisão manual. Erro de entrada,
leitura ou gravação encerra com código diferente de zero. Após cálculo válido,
o arquivo de saída existente pode ser substituído; em caso de erro, ele deve
permanecer intacto.

## 9. Critérios de aceite

O sistema está pronto quando:

- [ ] A CLI valida o formato de entrada e grava o schema de saída definido nesta
      spec, preservando a ordem e a justificativa por despesa.
- [ ] Erros estruturais interrompem o lote sem saída parcial; recusas de negócio
      e revisões manuais por item não impedem a avaliação das demais despesas.
- [ ] Cada regra de negócio definida tem critério de aceite numérico e teste
      automatizado correspondente, incluindo fronteiras e precedência.
- [ ] A referência temporal usada no cálculo aparece em `data_calculo` na saída.
- [ ] `motivos` nunca está vazio; contém todos os códigos das tratativas
	aplicadas em ordem e usa `revisao_manual_viagem` para qualquer revisão.
- [ ] Lote sem despesas produz `despesas: []` e totais `"0.00"`; a versão do
	contrato de saída é `"1.0"`.
- [ ] O README do produto descreve como executar e testar a aplicação.

## 10. O que fica em aberto

Permanecem pendentes as escolhas de stack/comandos de execução e o requisito do
envelope do Dia 2. A relação entre `periodo.inicio`/`periodo.fim` e a regra dos
90 dias está definida nesta versão: o período é metadado do lote, e a elegibilidade
temporal é determinada exclusivamente pela idade da despesa em relação à data
local do cálculo. Qualquer mudança futura deve ser registrada em
`DECISIONS.md` antes de implementar.
