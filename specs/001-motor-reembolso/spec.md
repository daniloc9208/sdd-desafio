# Spec — Motor de Cálculo de Reembolso

**Versão:** 0.8 · **Status:** decisões do envelope validadas; pronta para implementação · **Última alteração:** 2026-10-16

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
- Não oferece interface de administração da política; a política e as taxas são
  fornecidas em arquivos externos para cada cálculo.
- Não calcula nem compensa estornos; valores negativos são recusados neste fluxo.
- Não determina automaticamente a quantidade de diárias de hospedagem nem
  conclui despesas que dependam de conferência manual.

## 4. Entrada e saída

**Entrada:** arquivo de despesas JSON no formato demonstrado em
`exemplos/despesas-exemplo.json`, acompanhado de um arquivo de política e um
arquivo de cotações. Os caminhos dos quatro arquivos são fornecidos à CLI. Todos
os campos da entrada de despesas, exceto `despesas[].moeda`, são obrigatórios e
devem ter os tipos e formatos abaixo.

O objeto raiz de despesas deve conter exatamente `colaborador`, `periodo` e
`despesas`. `colaborador` deve conter exatamente `id`, `nome` e `centro_custo`;
`periodo`, exatamente `competencia`, `inicio` e `fim`. Cada item de `despesas`
deve conter exatamente os campos de despesa definidos na tabela, exceto
`moeda`, que é opcional.

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
| `despesas[].valor` | número decimal finito | Valor na moeda informada; pode ter mais de duas casas | Sim |
| `despesas[].moeda` | string com exatamente três letras ASCII maiúsculas | Moeda do valor; lista ISO 4217 não é consultada; quando ausente, assume `BRL` | Não |
| `despesas[].tem_nota_fiscal` | booleano | Indica se foi informada nota fiscal | Sim |

O documento, `colaborador`, `periodo` e cada item de `despesas` devem conter
somente os campos definidos nesta tabela. Propriedade adicional em qualquer
um desses níveis é erro estrutural e interrompe o lote.

O objeto raiz da política deve conter exatamente `versao`, `vigencia`,
`moeda_base`, `padrao`, `centros_custo`,
`nota_fiscal_obrigatoria_acima_de` e `acrescimo_em_viagem_percentual`.
`versao` é uma string não vazia após remover espaços externos, usada como
metadado; qualquer valor é aceito
quando o restante do arquivo satisfaz este schema. `vigencia` é data válida
`AAAA-MM-DD`;
`moeda_base` é `BRL`; `nota_fiscal_obrigatoria_acima_de`, cada `limite` e
`acrescimo_em_viagem_percentual` são números decimais finitos não negativos.
`padrao` e `centros_custo` são objetos de
categoria para regra. Cada regra contém exatamente `limite`,
`periodicidade` e, opcionalmente, `observacao`; `periodicidade` é `dia` ou
`diaria`, e `observacao`, quando presente, é string não vazia após remover
espaços externos. Chaves de categoria e de centro de custo devem ser strings
não vazias após remover espaços externos. Chaves de categoria são normalizadas
como categoria de despesa; chaves de centro, como centro de custo; colisões
após normalização invalidam a política. O marcador
`nao reembolsavel`, sem diferenciar caixa e removendo espaços externos, só é
válido junto de limite zero. Limite zero causa recusa conforme RN-012,
independentemente de haver observação.

O objeto raiz do arquivo de câmbio deve conter exatamente `moeda_base`, `taxas`
e, opcionalmente, `fonte` e `observacao`; a moeda-base é `BRL` e metadados
opcionais são strings não vazias após remover espaços externos. `taxas` é um
objeto indexado por datas válidas `AAAA-MM-DD`. Cada valor é um objeto que
mapeia códigos de três letras ASCII
maiúsculas a números decimais finitos positivos. Cada taxa expressa BRL por uma
unidade da moeda cotada. `BRL` tem taxa unitária implícita; se aparecer no
arquivo, seu valor deve ser numericamente igual a 1. O formato do código da
moeda é validado, mas sua presença na lista oficial ISO 4217 não é consultada:
moeda estrangeira sem taxa elegível é tratada por RN-013 como recusa individual.

Arquivos de despesas, política ou câmbio inválidos, incompletos, com tipos
incorretos, chaves extras ou chaves repetidas são erros estruturais e
interrompem o lote.
Os caminhos de despesas, política, câmbio e saída devem identificar quatro
arquivos distintos; dois caminhos que identifiquem o mesmo arquivo são inválidos.

**Saída:** JSON UTF-8 gravado no caminho indicado. Valores monetários são
representados como strings decimais BRL com duas casas, exceto `valor_original`,
que preserva a precisão decimal de entrada.

O objeto raiz da saída contém exatamente `versao_schema`, `data_calculo`,
`moeda`, `colaborador`, `periodo`, `despesas` e `totais`. `totais` contém
exatamente `valor_reembolsavel` e `valor_em_revisao`. Cada resultado de
despesa contém exatamente os campos `id`, `status`, `valor_informado`,
`valor_original`, `moeda_original`, `valor_reembolsavel` e `motivos`; cada item
de `motivos` contém exatamente `codigo` e `descricao`. `colaborador` e
`periodo` preservam os objetos da entrada.

| Campo | Tipo | Significado |
|---|---|---|
| `versao_schema` | string | Sempre `2.0` para este contrato |
| `data_calculo` | data `AAAA-MM-DD` | Data local capturada no início da execução; referência única da regra de 90 dias para todo o lote |
| `moeda` | string | Sempre `BRL` |
| `colaborador` | objeto | Identificação do colaborador recebida na entrada |
| `periodo` | objeto | Competência e intervalo recebidos na entrada |
| `despesas` | lista | Um resultado por despesa, preservando a ordem de entrada |
| `despesas[].id` | string | Identificador original da despesa |
| `despesas[].status` | string | `reembolsada`, `reembolsada_parcialmente`, `recusada` ou `revisao_manual`; revisão não é aprovação |
| `despesas[].valor_informado` | string decimal ou `null` | Valor original convertido para BRL, com duas casas, sempre que houver cotação utilizável, mesmo que a despesa seja recusada por outra regra; `null` somente quando não houver cotação utilizável |
| `despesas[].valor_original` | string decimal | Valor original da entrada, preservando sua precisão decimal |
| `despesas[].moeda_original` | string | Moeda informada ou `BRL` quando ausente |
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
`nota_fiscal_ausente`, `cotacao_indisponivel`,
`limite_zero_nao_reembolsavel`, `revisao_manual_viagem`, `limite_aplicado`,
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
	"versao_schema": "2.0",
	"data_calculo": "2026-10-16",
	"moeda": "BRL",
	"colaborador": { "id": "c-0417", "nome": "Marina Volpi", "centro_custo": "CC-ENG-PLATAFORMA" },
	"periodo": { "competencia": "2026-07", "inicio": "2026-07-01", "fim": "2026-07-31" },
	"despesas": [
		{
			"id": "d-014",
			"status": "reembolsada_parcialmente",
			"valor_informado": "81.00",
			"valor_original": "81.00",
			"moeda_original": "BRL",
			"valor_reembolsavel": "75.00",
			"motivos": [
				{ "codigo": "limite_aplicado", "descricao": "Valor limitado ao teto de R$ 75,00 do centro de custo." }
			]
		}
	],
	"totais": { "valor_reembolsavel": "75.00", "valor_em_revisao": "0.00" }
}
```

## 5. Regras de negócio

Cada regra recebe um ID (`RN-001`, ...). As tasks vão referenciar esses IDs.

### RN-001 — Limites por despesa

**Regra:** selecionar o limite aplicável pela RN-012. O limite é individual por
despesa (refeição, trecho ou unidade definida pela categoria), sem soma diária
nem cota compartilhada. Os limites da política são em BRL.
**Origem:** comunicado do RH, política v4; decisões AMB-001 e ENV-001.
**Aceite:** alimentação do `CC-COMERCIAL` pode reembolsar até R$ 90,00 por
despesa; transporte do `CC-ADM` pode reembolsar até R$ 60,00, antes de eventual
ampliação por viagem.

### RN-002 — Reembolso limitado ao teto

**Regra:** para despesa elegível acima do limite aplicável, reembolsar o menor
entre o valor informado e o teto; o excedente não é reembolsado.
**Origem:** política do RH, item 4; decisão AMB-002.
**Aceite:** alimentação de R$ 90,00 no `CC-ENG-PLATAFORMA`, com teto de
R$ 75,00 na política v4, resulta em R$ 75,00.

### RN-003 — Nota fiscal

**Regra:** despesa cujo equivalente em BRL, antes do arredondamento de
apresentação, seja maior ou igual ao limite configurado no arquivo de política
exige nota fiscal. Sem nota, a despesa é recusada integralmente.
**Origem:** comunicado do RH, política v4; decisões AMB-003 e ENV-006.
**Aceite:** valor convertido de R$ 100,00 sem nota é recusado; R$ 99,99 sem nota
não é recusado por esta regra.

### RN-004 — Identificação e limites de viagem

**Regra:** cada despesa de categoria normalizada `hospedagem`, com data válida e
valor positivo, gera como data de viagem o dia calendário seguinte, mesmo que a
categoria não tenha regra aplicável na política. Esse indício permanece válido
mesmo que a hospedagem seja depois recusada por categoria, duplicidade, prazo,
cotação indisponível ou falta de nota fiscal. Despesas elegíveis de outras
categorias cuja data coincida com pelo menos uma dessas datas recebem limite aumentado em 50%; o
aumento é aplicado uma única vez, ainda que mais de uma hospedagem gere a mesma
data. Cada despesa tem seu próprio teto ampliado, sem soma diária. Se o lote
contiver hospedagem e uma despesa elegível não estiver em nenhuma data de viagem
identificada, ela fica em `revisao_manual`, sem receber limite normal nem
ampliado. A própria hospedagem fica em `revisao_manual`, pois a entrada não
permite determinar as diárias, exceto quando a política explicitamente a marcar
como não reembolsável; nesse caso, a recusa automática prevalece. Sem nenhuma
hospedagem com data válida e valor original positivo, não há inferência de
viagem nem revisão manual por esse motivo.
**Origem:** política do RH e política v4; decisões AMB-004, AMB-008, AMB-021,
ENV-010 e ENV-018.
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
numericamente igual antes de arredondar, moeda original, descrição e fornecedor
iguais são duplicatas. Para descrição e fornecedor, comparar o texto exatamente
como recebido. Valores `54.90` e `54.9` na mesma moeda são iguais; moedas
diferentes ou valores originais diferentes não são duplicatas mesmo se seus
equivalentes em BRL coincidirem.
Manter a primeira na ordem do arquivo e recusar as seguintes. O formato atual
não tem anexo, portanto anexo não participa da comparação.
**Origem:** política do RH, item 8; decisões AMB-006 e ENV-008.
**Aceite:** entre dois itens com os mesmos campos-chave e `54.90`/`54.9` na
mesma moeda, manter o primeiro e recusar o segundo. Um valor `10 EUR` não é
duplicata de `10 USD`, ainda que a conversão produza o mesmo valor em BRL.

### RN-007 — Categorias

**Regra:** comparar categoria após remover espaços externos e converter para
minúsculas. Uma categoria é aplicável se existir na política específica do
centro de custo ou na política padrão. Se não existir em nenhuma dessas tabelas,
a despesa é recusada com motivo `categoria_fora_politica`.
**Origem:** comunicado do RH, política v4; decisões AMB-007 e ENV-001.
**Aceite:** `ALIMENTACAO` é reconhecida como `alimentacao`; `representacao` é
aplicável ao `CC-COMERCIAL`; categoria sem regra no centro nem no padrão é
recusada.

### RN-008 — Valores positivos e estornos fora de escopo

**Regra:** valor original zero é inválido e valor original negativo é recusado
neste fluxo. Para BRL, ou após conversão de moeda estrangeira, valor positivo
que arredondado para duas casas resulte em R$ 0,00 é recusado por ser inferior
a um centavo reembolsável. Estornos devem ser tratados em fluxo separado; não
reduzem nem aumentam o total deste cálculo. A invalidez afeta apenas a despesa,
permitindo avaliar as demais despesas válidas do lote.
**Origem:** decisões AMB-009 e contrato validado pelo responsável do produto.
**Aceite:** d-009, de R$ -45,00, é recusada com `valor_negativo_fora_escopo`; um
valor zero é recusado com `valor_zero_invalido`; R$ 0,004 é recusado com
`valor_inferior_ao_centavo`; nenhuma dessas recusas altera o total.
R$ 0,005 arredonda para R$ 0,01 e não é recusado por ser inferior a um centavo.

### RN-009 — Precisão monetária

**Regra:** manter precisão decimal durante conversão e cálculos; arredondar cada
valor monetário em BRL apresentado por despesa para duas casas: terceiro
algarismo decimal de 0 a 4 arredonda para baixo; de 5 a 9, para cima. O valor
original é preservado com sua precisão decimal. Os totais são a soma dos valores
por despesa já arredondados, inclusive o total em revisão manual.
**Origem:** decisões AMB-010 e ENV-007 e contrato validado pelo responsável.
**Aceite:** R$ 33,333 resulta em R$ 33,33; R$ 33,335 resulta em R$ 33,34. Os
totais conferem com a soma dos valores por despesa exibidos.

### RN-010 — Interface de cálculo

**Regra:** a aplicação recebe um arquivo JSON por meio do comando
`reembolso calcular --input despesas.json --output resultado.json --policy politica.json --exchange-rates cambio.json`
e grava um resultado JSON no caminho indicado. Os quatro caminhos são
obrigatórios. Erro de leitura ou validação de qualquer entrada/configuração
interrompe o lote sem resultado parcial; erro preserva a saída preexistente.
**Origem:** interface do desafio e decisões ENV-011.
**Aceite:** a execução com os caminhos de entrada, saída, política e câmbio
informados produz um arquivo JSON válido segundo o contrato desta seção.

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

### RN-012 — Política por centro de custo

**Regra:** carregar a política do arquivo informado em cada execução. A política
informada deve estar vigente na data local de envio do pedido, representada por
`data_calculo`; se `data_calculo` for anterior a `vigencia`, rejeitar a
configuração e interromper o lote. A data da despesa não escolhe a versão da
política: uma política vigente no envio aplica-se a todo o lote, inclusive
despesas ocorridas antes de sua vigência. Normalizar o centro de custo removendo
espaços externos e ignorando caixa para localizar a tabela correspondente.
Chaves de centros que colidam após essa normalização tornam a política inválida.
Se o centro não existir, usar `padrao` integralmente. Se existir, selecionar
primeiro sua regra para a categoria; quando ausente, usar a regra padrão da
mesma categoria. Categorias sem regra no centro e no padrão são recusadas com
`categoria_fora_politica`. Qualquer regra aplicável com limite zero causa recusa
automática antes da revisão manual, com motivo `limite_zero_nao_reembolsavel`.
Se a regra tiver `observacao` igual a `nao reembolsavel`, ignorando caixa e
espaços externos, o limite obrigatoriamente é zero; marcador com limite
positivo torna a política inválida. Para os demais casos, a RN-004 continua
determinando revisão manual quando as diárias não puderem ser determinadas. Os
limites e a exigência de nota fiscal estão em BRL.
**Origem:** comunicado do RH, Política v4; decisões ENV-001, ENV-010, ENV-013,
ENV-014, ENV-016 e ENV-017.
**Aceite:** alimentação do `CC-COMERCIAL` usa R$ 90,00; hospedagem de
`CC-ENG-PLATAFORMA` é recusada automaticamente; categoria sem regra no centro
nem no padrão é recusada; centro não cadastrado usa os limites padrão; centros
`CC-COMERCIAL`, `cc-comercial` e ` CC-COMERCIAL ` resolvem à mesma tabela.

### RN-013 — Conversão de moeda estrangeira

**Regra:** interpretar ausência de `moeda` como `BRL`. Validar em `moeda`
somente o formato de três letras ASCII maiúsculas; não consultar uma lista
externa de códigos ISO. Para moeda estrangeira, converter o valor original para
BRL multiplicando-o pela cotação de venda PTAX de fechamento mais recente
daquela moeda, em data igual ou anterior à data da despesa. A busca é feita
entre as datas que contenham cotação para aquela moeda; nunca usar cotação
futura. Manter precisão decimal
durante a multiplicação e arredondar somente os valores monetários finais por
despesa conforme RN-009. A cotação é aplicada antes dos limites e da exigência
de nota fiscal. Preencher `valor_informado` sempre que houver cotação utilizável,
mesmo que outra regra venha a recusar a despesa; isso não altera a ordem de
precedência das recusas. Se nenhuma cotação anterior ou do mesmo dia existir
para a moeda, `valor_informado` é `null`; aplicar a recusa
`cotacao_indisponivel` na ordem definida na seção 8. `BRL` sempre usa taxa
unitária e não depende de entrada na tabela.
**Origem:** comunicado do RH, Política v4; decisões ENV-002 a ENV-009,
ENV-015, ENV-019 e ENV-020.
**Aceite:** despesa de 10 EUR em data cuja taxa é 5,90 resulta em equivalente
R$ 59,00 antes de limites; despesa de sábado sem cotação nesse dia usa a última
cotação anterior; nenhuma cotação disponível gera recusa individual e
`valor_informado: null`.

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

### AMB-011 — Precedência das políticas por centro de custo

**Texto original do RH:** os limites variam por centro de custo; centros sem
entrada usam a política padrão.
**O que não está claro:** como compor uma tabela de centro conhecida que não
tenha uma categoria e como tratar categoria sem regra em nenhuma das tabelas.
**Decisão:** centro ausente usa a tabela padrão inteira; centro conhecido usa a
regra própria da categoria e, se ausente, a regra padrão da mesma categoria.
Sem regra em ambas, recusar apenas a despesa como categoria sem política
aplicável.
**Justificativa:** aplica a orientação explícita de fallback sem herdar regras
de outro centro de custo.
**Regra afetada:** RN-007 e RN-012.

### AMB-012 — Cotação ausente na data da despesa

**Texto original do RH:** usar a taxa da data da despesa; as taxas são
publicadas apenas em dias úteis bancários.
**O que não está claro:** como converter despesas em fim de semana/feriado ou
quando a cotação da data não estiver registrada.
**Decisão:** usar a cotação PTAX de fechamento de venda mais recente para a
moeda, na própria data da despesa ou antes dela; nunca usar cotação futura.
**Justificativa:** resolve datas sem publicação bancária sem buscar taxa atual
nem introduzir dependência de rede.
**Regra afetada:** RN-013.

### AMB-013 — Moeda sem cotação disponível

**Texto original do RH:** a entrada pode conter moedas ISO 4217; a conversão
usa as taxas fornecidas.
**O que não está claro:** como proceder quando não existe cotação anterior ou
do mesmo dia para a moeda.
**Decisão:** manter o cálculo offline e recusar somente a despesa com
`cotacao_indisponivel`. Preservar o valor/moeda originais e representar
`valor_informado` em BRL como `null`.
**Justificativa:** não inventar taxa e não impedir a avaliação dos demais itens.
**Regra afetada:** RN-013 e contrato de saída.

### AMB-014 — Base de cálculo e rastreabilidade monetária

**Texto original do RH:** limites são em BRL e despesas podem ser estrangeiras.
**O que não está claro:** quando converter em relação à nota fiscal, à
duplicidade e ao arredondamento, e como apresentar as duas moedas.
**Decisão:** converter antes de testar limite e nota fiscal; usar o equivalente
em BRL, sem arredondamento intermediário. Duplicidade inclui moeda e valor
originais. Na saída, `valor_informado` é o equivalente BRL, acompanhado de
`valor_original` com precisão integral e `moeda_original`. Incompatibilidade do
contrato eleva `versao_schema` para `"2.0"`.
**Justificativa:** conserva precisão de cálculo e auditabilidade do lançamento.
**Regra afetada:** RN-003, RN-006, RN-009, RN-013 e contrato de saída.

### AMB-015 — Política explicitamente não reembolsável

**Texto original do RH:** `CC-ENG-PLATAFORMA` não reembolsa hospedagem de forma
alguma.
**O que não está claro:** se qualquer limite zero significa recusa e se uma
observação não reembolsável pode coexistir com limite positivo.
**Decisão:** qualquer regra aplicável com limite zero recusa automaticamente a
despesa antes da revisão manual. O marcador opcional
`observacao: "nao reembolsavel"` também exige limite zero; se acompanhar limite
positivo, a política é inválida.
**Justificativa:** impede que um zero produza status de reembolso parcial com
valor zero e trata a proibição expressa antes de qualquer revisão.
**Regra afetada:** RN-004 e RN-012.

### AMB-016 — Localização das configurações externas

**Texto original do RH:** política e cotações são arquivos externos ao código.
**O que não está claro:** como o operador indica os arquivos usados em cada
cálculo.
**Decisão:** exigir as opções `--policy` e `--exchange-rates` em cada execução.
**Justificativa:** torna explícitas as versões de política e cotações usadas e
permite atualizar arquivos sem alterar o código.
**Regra afetada:** RN-010 e RN-012.

### AMB-017 — Vigência e lançamentos retroativos

**Texto original do RH:** política v4 tem vigência imediata e é retroativa à
competência atual.
**O que não está claro:** se a data da despesa ou a data de envio do pedido
determina a política aplicável.
**Decisão:** `data_calculo` é a data local atual em que o pedido é enviado. A
política informada precisa estar vigente nessa data; se ainda não estiver, o
arquivo é rejeitado. Quando vigente no envio, aplica-se a todas as despesas do
lote, mesmo que tenham ocorrido antes da vigência.
**Justificativa:** representa a retroatividade indicada pelo RH sem inventar
uma data de lançamento que não existe no contrato de entrada.
**Regra afetada:** RN-005 e RN-012.

### AMB-018 — Normalização de centro de custo

**Texto original do RH:** a tabela de limites é indexada por centro de custo.
**O que não está claro:** se caixa e espaços externos alteram a identificação.
**Decisão:** remover espaços externos e ignorar maiúsculas/minúsculas para
comparar o centro de custo recebido com as chaves da política. Preservar o valor
original na saída. Chaves de política que colidam após normalização invalidam
o arquivo.
**Justificativa:** evita fallback acidental por diferenças de formatação e
evita precedência ambígua entre chaves duplicadas.
**Regra afetada:** RN-012.

### AMB-019 — Códigos de moeda

**Texto original do RH:** o campo de moeda é ISO 4217.
**O que não está claro:** se a lista de códigos é validada contra catálogo
externo ou se apenas o formato é validado.
**Decisão:** exigir exatamente três letras ASCII maiúsculas, sem consulta a
catálogo externo. Se a moeda não tiver cotação elegível no arquivo, recusar
somente o item com `cotacao_indisponivel`.
**Justificativa:** preserva execução offline e deixa a cotação fornecida como
autoridade operacional para as moedas suportadas.
**Regra afetada:** entrada e RN-013.

### AMB-020 — Versão declarada da política

**Texto original do envelope:** a política contém um campo `versao`.
**O que não está claro:** se o motor deve aceitar apenas uma versão nominal
conhecida ou validar a estrutura do arquivo independentemente desse rótulo.
**Decisão:** tratar `versao` como metadado: exigir uma string não vazia após
remover espaços externos, mas não rejeitar rótulos desconhecidos quando o arquivo satisfizer o schema definido
nesta spec.
**Justificativa:** o formato e as regras são validados pelo schema; o rótulo,
sozinho, não altera a interpretação da política.
**Regra afetada:** contrato de política da seção 4 e RN-012.

### AMB-021 — Sinal de viagem sem regra de política

**Texto original do envelope:** uma despesa de hospedagem indica viagem.
**O que não está claro:** se a categoria precisa ter regra aplicável na
política para produzir esse indício.
**Decisão:** qualquer despesa estruturalmente válida com categoria normalizada
`hospedagem`, data válida e valor original positivo gera o dia seguinte como
data de viagem, ainda que depois seja recusada por não haver regra para a
categoria.
**Justificativa:** a hospedagem informa o contexto da viagem, independentemente
de sua elegibilidade para reembolso.
**Regra afetada:** RN-004 e ordem de aplicação, passo 2.

### AMB-022 — Valor convertido em despesas recusadas

**Texto original do envelope:** a saída preserva o valor original e apresenta
`valor_informado` em BRL, ou `null` quando não há cotação.
**O que não está claro:** se `valor_informado` deve ser calculado quando outra
regra já é suficiente para recusar a despesa.
**Decisão:** calcular e apresentar o equivalente BRL sempre que houver cotação
utilizável, mesmo para despesas recusadas por outra regra. `null` significa
exclusivamente ausência de cotação utilizável; a prioridade das razões de
recusa segue a ordem da seção 8.
**Justificativa:** mantém o valor monetário auditável sem mudar a decisão ou a
precedência de regras.
**Regra afetada:** contrato de saída, RN-009, RN-013 e ordem de aplicação.

### AMB-023 — Taxa explícita para BRL

**Texto original do envelope:** BRL é a moeda-base e não exige cotação no
arquivo.
**O que não está claro:** se uma taxa explícita para BRL é permitida e como
interpretar um valor diferente de 1.
**Decisão:** permitir taxa explícita para BRL somente se for numericamente
igual a 1; rejeitar o arquivo de câmbio se o valor diferir. O cálculo sempre
usa taxa unitária para BRL.
**Justificativa:** mantém o comportamento da moeda-base inequívoco e permite
arquivos que listem explicitamente a unidade-base.
**Regra afetada:** contrato do arquivo de câmbio e RN-013.

---

## 7. Casos de borda

Os casos abaixo usam `politica-v4.json`, `cambio.json` e
`data_calculo: 2026-07-31`. Casos de limite descritos como isolados não incluem
hospedagem no lote; os casos de viagem indicam explicitamente as hospedagens
presentes. Os resultados do lote completo são especificados em T-018.

| Caso | Entrada | Comportamento esperado (data de cálculo 2026-07-31) | Regra |
|---|---|---|---|
| Despesas de alimentação no mesmo dia, lote isolado | d-001 e d-002 em `CC-ENG-PLATAFORMA` | Aplicar teto por despesa de R$ 75,00: reembolsar R$ 72,50 e R$ 38,00 | RN-001, RN-012 |
| Transporte sem nota a partir de R$ 100 | d-003 e d-004 | Recusar ambas por falta de nota fiscal | RN-003 |
| Categoria fora da política | d-005 (`coworking`) | Recusar com motivo `categoria_fora_politica` | RN-007 |
| Duplicatas de negócio, lote isolado | d-006 e d-007 | Manter d-006; recusar d-007 como duplicata | RN-006 |
| Despesa com mais de 90 dias | d-008 | Recusar por prazo; diferença de 107 dias | RN-005 |
| Valor negativo | d-009 | Recusar apenas d-009; não alterar os demais resultados | RN-008 |
| Hospedagem proibida na política | d-010 em `CC-ENG-PLATAFORMA` | Recusar antes da revisão manual com `limite_zero_nao_reembolsavel`; ainda gera o dia de viagem 2026-07-15 | RN-004, RN-012 |
| Café da manhã no dia seguinte à primeira hospedagem | d-011 com hospedagem em d-010 | Teto de viagem R$ 112,50; reembolso R$ 33,33; motivos `limite_viagem_aplicado` e `dentro_do_limite` | RN-004, RN-009, RN-012 |
| Despesa em sábado com hospedagens no lote | d-012 | Status `revisao_manual`, pois não ocorre no dia seguinte a nenhuma hospedagem | RN-004 |
| Categoria com caixa diferente e hospedagens no lote | d-014 (`ALIMENTACAO`) | Status `revisao_manual`, pois não ocorre no dia seguinte a nenhuma hospedagem | RN-004, RN-007 |
| Hospedagem sem nota acima de R$ 100 | d-013 | Recusar por falta de nota; ainda gera dia de viagem em 2026-07-23 | RN-003, RN-004 |
| Múltiplas hospedagens | d-010 e d-013 | Geram dias de viagem distintos: 2026-07-15 e 2026-07-23; recusa posterior de d-013 não remove o segundo dia | RN-004 |
| Dia seguinte à segunda hospedagem | Despesa elegível em 2026-07-23 | Teto ampliado é o limite da categoria/centro × 1,5: alimentação CC-COMERCIAL R$ 135,00; transporte CC-ENG-PLATAFORMA R$ 120,00 | RN-004, RN-012 |
| Duas refeições no mesmo dia de viagem | Duas despesas elegíveis de alimentação em `CC-COMERCIAL` em 2026-07-15 | Cada despesa pode reembolsar até R$ 135,00; não há agregação diária | RN-001, RN-004, RN-012 |
| Limite parcial em viagem | Despesa de alimentação de R$ 150,00 em 2026-07-15, com nota e `CC-COMERCIAL` | Limite ampliado R$ 135,00; status parcial; motivos `limite_viagem_aplicado` e `limite_aplicado` | RN-002, RN-004, RN-012 |
| Lista de despesas vazia | `despesas: []` | Saída com lista vazia e ambos totais em `"0.00"` | Contrato de saída |
| Competência e início coerentes | `competencia: "2026-07"`, início `2026-07-01`, fim `2026-08-15` | Lote aceito | RN-011 |
| Início em competência diferente | `competencia: "2026-07"`, início `2026-06-30` | Lote rejeitado sem resultado | RN-011 |
| Versão do schema | Qualquer lote estruturalmente válido | `versao_schema` é exatamente `"2.0"` | Contrato de saída |
| Centro de custo não cadastrado | `despesas-envelope-cc-desconhecido.json` | Usar limites de `padrao` | RN-012 |
| Centro conhecido sem regra da categoria | categoria sem regra própria, presente em `padrao` | Usar o limite padrão dessa categoria | RN-012 |
| Categoria sem regra específica nem padrão | `representacao` em centro sem regra aplicável | Recusar com `categoria_fora_politica` | RN-007, RN-012 |
| Hospedagem não reembolsável | `CC-ENG-PLATAFORMA`, categoria `hospedagem` | Recusar automaticamente, sem revisão manual | RN-004, RN-012 |
| Hospedagem sem regra aplicável | Categoria `hospedagem`, data válida, valor positivo, mas sem regra no centro nem no padrão | Recusar por `categoria_fora_politica`, mas ainda gerar o dia seguinte como data de viagem | RN-004, RN-007 |
| Rótulo de versão desconhecido | `versao` não vazia após remover espaços externos e diferente de `v4`, restante da política válido | Aceitar a política pelo schema; tratar o rótulo como metadado | RN-012 |
| Conversão em despesa recusada | Despesa estrangeira com cotação válida, mas recusada por outra regra | Informar equivalente BRL em `valor_informado`; manter status e motivos da regra impeditiva | RN-013 |
| Taxa explícita para BRL | Arquivo inclui `BRL: 1` | Aceitar e continuar usando taxa unitária | RN-013 |
| Taxa BRL diferente de 1 | Arquivo inclui `BRL` com valor diferente de 1 | Rejeitar o arquivo de câmbio | RN-013 |
| Limite zero sem observação | Regra aplicável de qualquer categoria com limite `0.00` | Recusar antes da revisão manual com `limite_zero_nao_reembolsavel` | RN-012 |
| Marcador não reembolsável com limite positivo | Regra com observação `nao reembolsavel` e limite maior que zero | Rejeitar arquivo de política; preservar saída existente | RN-012 |
| Pedido após vigência com despesa antiga | `data_calculo` após a vigência e despesa anterior a ela | Aplicar a política informada, desde que vigente no envio | RN-012 |
| Pedido antes da vigência | `data_calculo` anterior a `politica.vigencia` | Erro de configuração, sem resultado | RN-012 |
| Centro de custo com variação de caixa/espaços | ` cc-comercial ` | Resolver como `CC-COMERCIAL`; preservar string original na saída | RN-012 |
| Chaves de centro que colidem normalizadas | Política tem `CC-ADM` e ` cc-adm ` | Rejeitar arquivo de política como ambíguo | RN-012 |
| Moeda com formato de três letras sem taxa | Código `GBP` e nenhuma taxa no arquivo atual | Recusar item com `cotacao_indisponivel`, sem buscar rede; o fixture recebido não é alterado | RN-013 |
| Taxa pesquisada, mas ausente do arquivo | GBP/BRL `6.79180` em 2026-07-21 consta na consulta PTAX, mas não no fixture | Não usar pesquisa externa no cálculo; recusar o item GBP com cotação indisponível | RN-013 |
| Despesa em moeda estrangeira | EUR 22,00 em 2026-07-14, taxa 5,93 | Equivalente `valor_informado` de `"130.46"` BRL antes de aplicar teto | RN-013 |
| Sem cotação na data | EUR em sábado 2026-07-18 | Usar última taxa disponível em ou antes da data, 2026-07-17 | RN-013 |
| Sem nenhuma cotação para moeda | Moeda sem entrada anterior ou no dia | Recusar item com `cotacao_indisponivel`; `valor_informado: null` | RN-013 |
| Chave de duplicidade internacional | Mesmos dados, valor numérico igual, moedas originais distintas | Não tratar como duplicatas | RN-006 |
| Rastreabilidade monetária | Despesa estrangeira convertida | Informar valor BRL, valor original sem perda de precisão e moeda original | Contrato de saída |
| Valor positivo abaixo de meio centavo | Despesa de R$ 0,004 | Recusar com `valor_inferior_ao_centavo`; valor reembolsável `"0.00"` | RN-008, RN-009 |
| Valor no meio centavo | Despesa de R$ 0,005 | Arredondar para R$ 0,01; não recusar por valor subcentavo | RN-008, RN-009 |
| Igualdade de valor para duplicidade | Valores `54.90` e `54.9` em despesas com os demais campos-chave iguais | Tratar como duplicatas | RN-006 |
| Valores distintos que exibem os mesmos centavos | `33.331` e `33.334` em despesas com os demais campos-chave iguais | Não tratar como duplicatas por valor | RN-006, RN-009 |
| Propriedade JSON desconhecida | Campo adicional em qualquer objeto da entrada | Interromper o lote sem saída parcial | Contrato de entrada |
| Dois caminhos apontam para o mesmo arquivo | Qualquer par entre despesas, política, câmbio e saída, inclusive aliases | Interromper sem alterar arquivo algum | RN-010 |

## 8. Ordem de aplicação das regras

As regras são aplicadas nesta ordem. A primeira regra impeditiva define o status
principal da despesa; a saída registra o motivo correspondente. A ordem da lista
é normativa:

1. Capturar a data local uma única vez no envio do pedido e registrá-la como
	`data_calculo`. Validar o documento de despesas, a política e as cotações,
	incluindo campos obrigatórios e ausência de propriedades não especificadas.
	Erro estrutural, campo ausente, tipo/formato inválido, ID repetido após
	remoção de espaços externos, início fora da competência ou fim anterior ao
	início interrompe o lote. A política deve estar vigente em `data_calculo`.
	Os caminhos de entrada, política, câmbio e saída devem ser distintos; em
	qualquer erro, não gerar resultado parcial nem alterar arquivos.
2. Para todas as despesas estruturalmente válidas, normalizar categoria e moeda
	e identificar as datas de hospedagem que geram viagem: cada item com categoria
	`hospedagem`, data válida e valor original positivo gera o dia calendário
	seguinte, mesmo que não tenha regra de política aplicável ou depois seja
	recusado. Datas repetidas geram um único dia de viagem; o aumento não acumula.
3. Para preencher `valor_informado`, converter cada despesa estruturalmente
	válida sempre que houver cotação utilizável, mesmo se outra regra recusar o
	item. Para definir status e motivos, recusar valor original zero/negativo e
	data futura antes de aplicar a recusa por cotação ausente. Converter moeda
	estrangeira usando a cotação PTAX de venda mais recente em ou antes da data
	da despesa; nenhuma consulta externa é feita. Manter precisão decimal na
	conversão. Se
	o equivalente BRL positivo arredondado conforme RN-009 resultar em `"0.00"`,
	recusar com `valor_inferior_ao_centavo`, sem arredondar intermediariamente
	o valor usado nas regras seguintes. Se não houver cotação utilizável, definir
	`valor_informado` como `null` e, se não houver recusa anterior, recusar com
	`cotacao_indisponivel`.
4. Validar a categoria normalizada contra a regra específica do centro de custo
	ou a regra padrão. Sem nenhuma regra aplicável, recusar a despesa.
	Qualquer regra aplicável com limite zero causa recusa com
	`limite_zero_nao_reembolsavel` antes das regras de duplicidade e revisão
	manual.
5. Detectar duplicatas entre despesas não recusadas, comparando categoria
	normalizada, data, valor original decimal, moeda original, descrição e
	fornecedor. Preservar a primeira na ordem de entrada.
6. Recusar despesa ocorrida há mais de 90 dias, comparando com a data local do
	cálculo. Exatamente 90 dias é elegível.
7. Exigir nota fiscal quando o equivalente BRL antes do arredondamento for
	maior ou igual ao limite da política; sem nota, recusar a despesa integral.
	Ao encontrar uma recusa nos passos 3–7, encerrar a avaliação daquele item,
	preservar os motivos registrados e continuar com os demais itens.
8. Para despesa não recusada, aplicar a política explicitamente não
	reembolsável antes da revisão manual. Caso contrário, hospedagem fica em
	`revisao_manual` por diária indeterminável; quando houver hospedagem no lote,
	itens elegíveis fora das datas de viagem ficam no mesmo status, sem limite
	normal nem ampliado.
9. Para as demais despesas elegíveis, selecionar o limite pela RN-012 e, se a
	data estiver no conjunto de dias de viagem, aplicar o acréscimo configurado.
	Reembolsar no máximo o equivalente BRL e registrar os motivos aplicáveis.
10. Arredondar valores finais BRL por despesa para duas casas e somar os valores
	já arredondados para formar os totais. Preservar o valor original na saída.

O código de saída da CLI é zero quando um resultado JSON completo foi gerado,
mesmo que existam despesas recusadas ou em revisão manual. Erro de entrada,
política, câmbio, leitura ou gravação encerra com código diferente de zero.
Após cálculo válido, o arquivo de saída existente pode ser substituído; em caso
de erro, ele deve permanecer intacto.

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
	contrato de saída é `"2.0"`.
- [ ] O README do produto descreve como executar e testar a aplicação.

## 10. O que fica em aberto

O item opcional do envelope sobre aprovação manual de despesas acima de R$ 500
fica fora desta entrega. A relação entre `periodo.inicio`/`periodo.fim` e a
regra dos 90 dias permanece definida: o período é metadado do lote e a
elegibilidade temporal é determinada exclusivamente pela idade da despesa em
relação à data local do cálculo. Mudanças futuras devem ser registradas em
`DECISIONS.md` antes de implementar.
