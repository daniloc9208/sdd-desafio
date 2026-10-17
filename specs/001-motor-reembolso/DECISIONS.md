# Log de Decisões e Mudanças de Spec

> Uma entrada **toda vez** que a spec mudar. Este arquivo é a prova de que a spec
> foi tratada como artefato vivo e não como cerimônia de abertura.
>
> Spec que não muda em dois dias é spec que ninguém consultou. Mudança não é
> demérito — mudança não registrada é.

Ordem cronológica inversa: a mais recente primeiro.

## D-007 — Taxa explícita para BRL · 2026-10-16

**Gatilho:** revisão do schema de câmbio da spec v0.7.

**O que mudou na spec:** a versão passou a 0.8. `BRL` continua tendo taxa
unitária implícita; o arquivo pode listar `BRL` explicitamente somente quando
seu valor numérico for igual a 1. Qualquer outro valor torna o arquivo de
câmbio inválido.

**Decisão do responsável:** permitir taxa explícita para BRL igual a 1 e
rejeitar valor diferente.

**Por quê:** permitir representação explícita da moeda-base sem ambiguidade na
conversão.

**Tasks afetadas:** T-023 e a matriz de cobertura.

**Custo:** revisão documental; implementação e testes ainda não executados.

## D-006 — Valor convertido em despesas recusadas · 2026-10-16

**Gatilho:** revisão do contrato de saída da spec v0.6 para esclarecer o valor
apresentado em despesas que não recebem reembolso.

**O que mudou na spec:** a versão passou a 0.7. `valor_informado` contém o
equivalente BRL sempre que houver cotação utilizável, mesmo se outra regra
recusar a despesa; `null` fica reservado à ausência de cotação. Essa conversão
para apresentação não altera a ordem de precedência das recusas.

**Decisão do responsável:** calcular e apresentar o equivalente BRL em toda
despesa com cotação utilizável, inclusive se recusada por outra regra.

**Por quê:** manter a rastreabilidade monetária sem mudar o resultado de
negócio.

**Tasks afetadas:** T-024 e a matriz de cobertura.

**Custo:** revisão documental; implementação e testes ainda não executados.

## D-005 — Rótulo da política e indício de viagem · 2026-10-16

**Gatilho:** revisão final da spec v0.5 antes de retomar a implementação.

**O que mudou na spec:** a versão passou a 0.6. O campo `versao` da política é
metadado e aceita qualquer string não vazia após remover espaços externos,
quando o restante do arquivo respeita o schema. Qualquer despesa estruturalmente válida de categoria
`hospedagem`, com data válida e valor original positivo, ativa o dia seguinte
como data de viagem, mesmo sem regra aplicável na política e ainda que depois
seja recusada. Os objetos de entrada e saída têm agora seus conjuntos exatos de
chaves descritos; JSON com chaves repetidas é erro estrutural. Chaves vazias de
categoria/centro são rejeitadas. A CLI passa a ser nomeada explicitamente como
`reembolso`, e os testes de tarefa refletem códigos de moeda sem consulta ao
catálogo ISO e colisões entre caminhos dos quatro arquivos.

**Decisões do responsável:** aceitar qualquer rótulo não vazio de `versao`
quando o schema for válido; hospedagem sem regra aplicável ainda indica viagem.

**Por quê:** eliminar interpretações diferentes durante validação da política e
identificação de viagem, além de alinhar o contrato de execução e os critérios
de teste aos requisitos já acordados.

**Tasks afetadas:** T-003, T-004, T-005, T-011, T-021 e T-023; matriz de
cobertura atualizada.

**Custo:** revisão documental; implementação e testes ainda não executados.

## D-004 — Política v4 e despesas internacionais · 2026-10-16

**Gatilho:** recebimento do envelope do Dia 2 e decisões do responsável
registradas em `pendencias.MD`.

**O que mudou na spec:** a spec passou de 0.4 para 0.5. Os limites e a exigência
de nota agora vêm de política externa por centro de custo; centros desconhecidos
usam a tabela padrão, centros conhecidos recorrem ao padrão quando lhes falta a
categoria, e categoria sem regra em nenhuma tabela é recusada. Qualquer limite
zero causa recusa automática antes da revisão manual; marcador
`nao reembolsavel` com limite positivo invalida a política.
A entrada admite `moeda` opcional (padrão `BRL`), com conversão para BRL pela
PTAX de venda de fechamento mais recente até a data da despesa. Não há consulta
de rede em runtime; sem taxa disponível, só o item é recusado. O arredondamento
ocorre depois da conversão e dos critérios monetários. Duplicatas incluem
moeda e valor originais. A saída preserva `valor_original` e `moeda_original`,
passa a registrar `valor_informado` convertido ou `null` sem taxa e eleva o
schema para `2.0`. A CLI exige caminhos explícitos de política e câmbio.

**Decisões do responsável:** tabela padrão inteira para centro desconhecido;
fallback categoria a categoria para centro conhecido; usar última cotação
disponível em data igual ou anterior; recusar item sem qualquer taxa; conversão
antes da regra de nota fiscal; preservar precisão até o arredondamento final;
moeda/valor originais na chave de duplicidade; qualquer limite zero recusa
antes de revisão manual; o marcador `nao reembolsavel` exige limite zero;
opções `--policy` e `--exchange-rates` obrigatórias; output schema `2.0`.
`data_calculo` representa a data local do envio do pedido: a política informada
deve estar vigente nessa data e aplica-se ao lote inteiro, mesmo às despesas
ocorridas antes da vigência. Centro de custo é comparado sem espaços externos e
sem diferenciar caixa; colisões nas chaves normalizadas invalidam a política.
Códigos de moeda são validados apenas por formato de três letras ASCII
maiúsculas, sem consulta a catálogo ISO.

**Dado verificado e limite de uso:** consulta à API oficial PTAX do Banco
Central retornou cotação de venda de fechamento GBP/BRL `6.79180` em
2026-07-21 (`https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoMoedaPeriodo(moeda=@moeda,dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)?@moeda='GBP'&@dataInicial='07-20-2026'&@dataFinalCotacao='07-21-2026'&$format=json`).
Por orientação do responsável, a cotação pesquisada **não** foi adicionada ao
fixture de câmbio. O arquivo de despesas permanece intacto e o item GBP do
exemplo será recusado com `cotacao_indisponivel`, conforme ENV-004/ENV-005.

**Vigência e zero:** política com vigência posterior a `data_calculo` é erro de
configuração. Qualquer regra aplicável com limite zero causa recusa com
`limite_zero_nao_reembolsavel` antes de duplicidade/revisão; marcador
`observacao: "nao reembolsavel"` com limite positivo torna a política inválida.

**Por quê:** possibilitar limites financeiros atualizáveis sem alterar código,
calcular moeda estrangeira com cotação histórica reproduzível e preservar
rastreabilidade sem depender de rede durante o cálculo.

**O que isso invalidou:** limites fixos e categorias embutidas; política fixa no
plano; pressuposto de que todo valor recebido já está em BRL; nota fiscal
avaliada sobre valor original não convertido; chave de duplicidade sem moeda;
schema de saída `1.0`; CLI sem caminhos para política e câmbio; suposição de que
a data da despesa determina a versão da política; consulta a taxa fora do
arquivo. O contrato e os critérios anteriores correspondentes precisam ser
substituídos, não mantidos em paralelo.

**Tasks afetadas:** T-002, T-003, T-004, T-005, T-007, T-008, T-010, T-013,
T-014, T-015, T-018, T-019 e T-020 devem incorporar o novo modelo, parsing,
serialização, CLI, cálculo e integração. As tasks T-001 e T-006, T-009, T-011,
T-012, T-016 e T-017 mantêm seu escopo funcional, mas precisam ser validadas
contra o contrato atualizado. Novas tasks do envelope começam em T-021.

**Custo:** a medir no relatório após implementação; tempo não medido.

## D-003 — Bordas contratuais e escolha de Python · 2026-10-16

**Gatilho:** aprovação do responsável para incorporar as bordas de contrato
recomendadas e escolha de Python como linguagem do projeto.

**O que mudou na spec:** a versão passou a 0.4. Valores positivos que arredondem
para R$ 0,00 são recusados; a avaliação de um item termina na primeira recusa,
com os motivos já aplicados preservados. Duplicatas comparam valores decimais
antes do arredondamento; propriedades JSON não previstas são rejeitadas; entrada
e saída não podem referir-se ao mesmo arquivo; e `data_calculo` é capturada uma
vez no início do lote. A escolha de Python foi registrada para orientar o plano,
sem fixar ainda versão, dependências ou comando de instalação.

**Por quê:** fechar bordas que poderiam levar a resultados de reembolso,
validação e proteção de arquivos diferentes entre implementações.

**O que isso invalidou:** nenhuma regra implementada ou teste existente; as
condições agora precisam ser incluídas nos critérios e testes de implementação.

**Tasks afetadas:** nenhuma task de implementação foi executada. O plano técnico
deve definir versão mínima de Python, CLI, arquitetura, modelo interno e testes.

**Custo:** três documentos atualizados (`spec.md`, `pendencias.MD` e este log);
tempo não medido.

## D-002 — Fechamento dos furos funcionais · 2026-10-16

**Gatilho:** respostas do responsável às lacunas funcionais identificadas na
revisão da spec v0.2 (FURO-001, FURO-002, FURO-003 e FURO-005 a FURO-011,
conforme os IDs registrados em `pendencias.MD`).

**O que mudou na spec:** a RN-004 e a ordem de aplicação agora definem que uma
hospedagem com categoria reconhecida, data válida e valor positivo continua
sinalizando viagem mesmo que seja recusada depois; cada hospedagem gera seu
próprio dia seguinte de viagem, com aumento de 50% não cumulativo e aplicado
por despesa. Motivos passam a ser obrigatórios e cumulativos, e revisão manual
usa status `revisao_manual` com o único código `revisao_manual_viagem`. A validação
do período exige que o ano/mês de `periodo.inicio` corresponda à competência;
o dia não precisa ser o primeiro do mês. `periodo.fim` pode avançar para mês
posterior, mas não pode ser anterior ao início. Também foram definidos o
resultado de lista vazia e o valor fixo `versao_schema: "1.0"`.

**Por quê:** eliminar comportamento indeterminado em lotes com múltiplas
hospedagens, recusas simultâneas, revisão manual, período e saída sem despesas.

**O que isso invalidou:** a regra anterior que não especificava hospedagens
recusadas ou múltiplas, a lista que permitia motivos de revisão separados para
hospedagem e viagem, e a ausência de resultados esperados para lista vazia e
versão do schema. Nenhum código ou teste de produto existia nesta etapa.

**Tasks afetadas:** nenhuma task de implementação foi executada. As tasks devem
ser definidas ou revisadas a partir da spec v0.3 antes de iniciar o código.

**Custo:** três documentos atualizados (`spec.md`, `pendencias.MD` e este log);
tempo não medido.

## D-001 — Decisões de negócio e contratos iniciais · 2026-10-15

**Gatilho:** respostas do responsável às ambiguidades e à proposta de contrato
de entrada/saída e precedência das regras.

**O que mudou na spec:** as AMB-001 a AMB-010 passaram de perguntas sem decisão
para regras explícitas em RN-001 a RN-010. Foram definidos prazo de 90 dias
contado da data da despesa até a data local do cálculo, recusa por item de
valores zero/negativos, tratamento de viagem e hospedagem, chave de duplicidade,
normalização de categorias e arredondamento por despesa. A spec também passou a
definir o contrato JSON, validação, ordem de aplicação e comportamento de erros.

**Por quê:** tornar as regras verificáveis e evitar decisões implícitas durante
a implementação.

**O que isso invalidou:** o texto provisório da spec que tratava essas regras
como pendentes, o exemplo anterior de saída e os casos de borda sem resultados
esperados. Nenhuma implementação ou teste existia nesta etapa.

**Tasks afetadas:** nenhuma task de implementação foi executada; atualizar ou
criar as tasks a partir da versão 0.2 da spec antes de codificar.

**Custo:** quatro arquivos documentais atualizados (`spec.md`, `pendencias.MD`,
`PRD.MD` e este log); tempo não medido.

## Registro futuro

Adicione uma nova entrada se a spec mudar novamente. A numeração continua em
D-005.
