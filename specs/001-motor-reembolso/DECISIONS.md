# Log de Decisões e Mudanças de Spec

> Uma entrada **toda vez** que a spec mudar. Este arquivo é a prova de que a spec
> foi tratada como artefato vivo e não como cerimônia de abertura.
>
> Spec que não muda em dois dias é spec que ninguém consultou. Mudança não é
> demérito — mudança não registrada é.

Ordem cronológica inversa: a mais recente primeiro.

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

Adicione uma nova entrada quando a spec mudar novamente, incluindo a mudança do
envelope do Dia 2. A numeração continua em D-003.
