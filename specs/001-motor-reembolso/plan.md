# Plano Técnico — Motor de Cálculo de Reembolso

**Versão:** 0.3 · **Status:** proposta · **Baseado na spec:** 0.8 · **Data:** 2026-10-16

> Aqui mora o COMO. Este arquivo pode e deve falar de linguagem, biblioteca e
> arquitetura. O que ele **não** pode é introduzir regra de negócio nova — se
> apareceu uma, ela pertence à `spec.md`.

---

## 1. Stack

| Escolha | O quê | Por quê | O que descartei e por quê |
|---|---|---|---|
| Linguagem | Python 3.11+; validar em Python 3.11 e 3.13 | Linguagem escolhida pelo responsável e disponível no ambiente; 3.11.9 e 3.13.2 estão instalados | Node/Go descartados para manter o trabalho na linguagem escolhida e evitar troca de stack durante o desafio |
| CLI e instalação | `argparse` da biblioteca padrão; pacote instalável por `pyproject.toml` com comando `reembolso` | Interface simples, sem dependência de runtime para argumentos; fornece o comando pedido pela spec | Typer/Click descartados para evitar dependências adicionais num CLI com um único subcomando |
| Testes | `pytest` | Fixtures e parametrização facilitam nomear casos pelos IDs RN/AMB e testar muitas fronteiras | `unittest` descartado por exigir mais estrutura para a mesma cobertura neste projeto |
| Parsing/validação | `json` e validação explícita do contrato | Biblioteca padrão; comportamento estrito e erros podem ser controlados conforme a spec | Pydantic descartado para evitar dependência de runtime e deixar as regras do contrato visíveis no projeto |
| Aritmética monetária | `decimal.Decimal`, carregando números JSON diretamente como Decimal | Preserva precisão decimal antes do arredondamento monetário normativo | `float` descartado por representar vários decimais em base binária e poder alterar limites/totais |
| Lint/format | Ruff | Uma ferramenta cobre lint e formatação, com configuração pequena | Ferramentas separadas descartadas para reduzir configuração e comandos |

O projeto não usa dependências de runtime além da biblioteca padrão. `pytest`,
`ruff` e `setuptools` são dependências de desenvolvimento/empacotamento
declaradas em `pyproject.toml`.

## 2. Arquitetura

```
argumentos CLI → leitura estrita de despesas, política e câmbio →
validação dos três contratos → caso de uso de cálculo →
serialização do resultado → gravação JSON
```

**Fronteiras:** o adaptador CLI lida com argumentos, data local de referência,
arquivos e códigos de saída. Adaptadores validam os JSON de despesas, política
e cotações e os convertem em modelos internos. O núcleo recebe esses modelos e
`data_calculo`, aplica as regras da spec e retorna decisões; não lê arquivos,
não consulta o relógio nem a rede, e não escreve no terminal. A saída só é
gravada após cálculo e serialização bem-sucedidos. A escrita usa um arquivo
temporário no diretório do destino e só publica o resultado depois que ele
estiver completo.

## 3. Modelo de dados

- `InputBatch`: colaborador, período e lista ordenada de despesas validadas.
- `Expense`: ID, data, categoria original e normalizada, descrição, fornecedor,
  `Decimal` do valor original, moeda original e indicador de nota fiscal.
- `Policy`: moeda-base, limites padrão, limites por centro de custo, limite de
  nota fiscal e percentual de viagem, lidos e validados do arquivo informado.
- `ExchangeRates`: moeda-base e taxas positivas `Decimal` agrupadas por data e
  código de moeda; conversão determina a taxa histórica elegível sem I/O.
- `ExpenseDecision`: ID, status da spec, valores informado/reembolsável como
  `Decimal` (valor informado anulável somente quando a cotação falta), valor e
  moeda originais, e lista ordenada de motivos (código e descrição). Calcular
  o valor informado sempre que houver cotação, mesmo quando a despesa for
  recusada por outra regra.
- `CalculationResult`: versão do schema, `data_calculo`, moeda, dados do lote,
  decisões por despesa e totais aprovados/em revisão.
- Os modelos não fazem leitura/escrita de arquivos. A serialização converte
  valores BRL para strings com duas casas, preserva a precisão decimal de
  `valor_original` e emite schema `2.0`.

## 4. Como política e câmbio são representados

O adaptador de configuração valida e converte `politica-v4.json` para um
`Policy` imutável; os limites e categorias não ficam embutidos no código. O
rótulo `versao` é metadado; o schema validado define a interpretação. O CLI
exige `--policy` e `--exchange-rates`. Cotações também são carregadas para um
modelo imutável; o núcleo escolhe a data mais recente que não ultrapasse a data
da despesa e calcula com `Decimal`. BRL usa taxa unitária; se listada no arquivo,
deve ser numericamente igual a 1. Não há consulta à rede durante execução.
Alterações de formato exigem atualizar o contrato, a validação e os testes.

## 5. Decisões técnicas

### DT-001 — Separação entre CLI e cálculo

**Contexto:** as regras de viagem, motivos acumulados e precedência podem mudar
sem que a interface de arquivos precise mudar.
**Decisão:** manter cálculo como caso de uso puro, separado da CLI e dos
adaptadores de JSON/arquivo.
**Alternativa descartada:** concentrar parsing, cálculo e gravação num único
comando; descartada por dificultar testes focados e alterações de regra.
**Consequência:** regras podem ser testadas com entrada validada e data fixa;
há tipos/adaptadores explícitos a manter em sincronia com a spec.

### DT-002 — `Decimal` desde o parsing

**Contexto:** a entrada aceita mais de duas casas e o arredondamento ocorre na
apresentação, não durante cada operação.
**Decisão:** configurar o parser JSON para construir `Decimal` para valores
numéricos e rejeitar constantes não finitas; não converter dinheiro para `float`.
**Alternativa descartada:** ler como `float` e converter depois, pois a
representação binária já pode ter perdido precisão.
**Consequência:** comparações com limites e duplicatas preservam o número
decimal original; saída monetária é formatada somente no adaptador de saída.

### DT-003 — Política externa validada

**Contexto:** os limites variam por centro de custo e são mantidos pelo
financeiro fora do código.
**Decisão:** ler política por arquivo CLI, validar seu contrato e materializar
um objeto imutável usado pelo cálculo.
**Alternativa descartada:** manter limites no núcleo, pois impediria atualizações
operacionais e contradiz a Política v4.
**Consequência:** arquivos inválidos falham antes de gravar; o mesmo núcleo pode
ser testado com diferentes tabelas, sem alteração de implementação.

### DT-004 — Empacotamento e ferramentas de desenvolvimento

**Contexto:** a CLI precisa ser executável pelo nome documentado e reprodutível
em ambiente limpo.
**Decisão:** `pyproject.toml` com layout `src/reembolso`, entry point `reembolso`
e dependências de desenvolvimento opcionais.
**Alternativa descartada:** depender do diretório atual ou de `PYTHONPATH` manual,
por tornar o comando mais frágil no README e nos testes.
**Consequência:** requer instalação editável do projeto no ambiente virtual; o
comando da CLI fica igual ao contrato e à documentação.

### DT-005 — Conversão histórica offline

**Contexto:** a conversão deve ser reproduzível e não pode usar cotação atual
nem depender de serviço remoto durante o cálculo.
**Decisão:** carregar cotações do arquivo passado à CLI e fazer busca pela data
elegível no núcleo; aritmética com `Decimal`.
**Alternativa descartada:** consultar API em tempo de execução, por introduzir
indisponibilidade de rede e resultados não determinísticos.
**Consequência:** o arquivo deve conter as taxas históricas necessárias; falta
de taxa para um item é resultado de negócio definido pela spec.

### DT-006 — Saída atômica e caminhos distintos

**Contexto:** uma falha de validação ou escrita não pode deixar resultado
parcial nem destruir uma saída anterior, e os quatro arquivos da execução
precisam ser distintos mesmo quando seus caminhos usam aliases.
**Decisão:** antes de ler ou gravar, resolver os quatro caminhos com
`Path.resolve(strict=False)` e compará-los com normalização específica do
sistema (`os.path.normcase`). Para caminhos que já existem, usar também
`os.path.samefile` para identificar aliases que apontem ao mesmo arquivo.
Escrever a saída completa em arquivo temporário exclusivo no mesmo diretório
do destino; depois de fechar o arquivo com sucesso, publicá-lo com
`os.replace`. Se qualquer etapa falhar, remover o temporário quando possível,
propagar um erro explícito e deixar a saída anterior intacta.
**Alternativa descartada:** gravar diretamente no destino ou usar temporário em
outro volume, pois a primeira opção expõe conteúdo parcial e a segunda não
permite contar com substituição atômica.
**Consequência:** a publicação é uma operação final e atômica no mesmo volume;
falhas durante a preparação ou substituição são reportadas e cobertas por
testes. A comparação de caminhos existentes também detecta hard links; para
caminhos ainda inexistentes, a comparação usa seus caminhos resolvidos e
normalizados.

## 6. Estratégia de testes

- **Nível:** maioria unitária para regras puras; integração da CLI para leitura,
  validação, escrita, códigos de saída e preservação de arquivos em erro.
- **Arquivos:** testar caminhos iguais por grafias diferentes, aliases
  existentes e erro durante a substituição; confirmar que saída preexistente
  permanece intacta e que temporários não são deixados após falhas recuperáveis.
- **Cobertura por requisito:** cada RN e cada caso da seção 7 da spec deve
  referenciar ao menos um teste na matriz de `tasks.md`.
- **Casos de borda:** parametrizar fronteiras de nota, prazo, arredondamento,
  duplicidade e limites; testar política específica/fallback, política zero,
  moeda BRL/estrangeira, cotação exata/anterior/ausente, valor informado em
  despesa recusada, taxa BRL explícita válida/inválida, viagens com uma e várias
  hospedagens, lote vazio, arquivos JSON inválidos e colisões de caminhos.
- **Relógio:** o núcleo recebe `data_calculo`; testes passam datas fixas e nunca
  dependem implicitamente do dia em que rodam.
- **Nomenclatura:** incluir ID da regra no nome, por exemplo
  `test_rn003_recusa_valor_100_sem_nota` e
  `test_furo002_duas_hospedagens_geram_dois_dias_de_viagem`.
- **Comandos:** `python -m pytest`, `ruff check .` e `ruff format --check .`.

## 7. Riscos

| Risco | Probabilidade | O que faço se acontecer |
|---|---|---|
| Divergência entre spec e política implementada | Média | Cobrir cada RN com teste nomeado e revisar o diff contra a spec antes de concluir a task |
| Data local torna elegibilidade variável | Média | Capturar `data_calculo` uma vez no início do CLI e injetar data fixa nos testes |
| Precisão monetária ou parsing introduz float | Média | Validar o parsing de decimais e testar limites/subcentavos usando `Decimal` |
| Configuração inválida altera o cálculo | Média | Validar política e taxas integralmente antes do início do cálculo e da gravação |
| Arquivo de câmbio não contém data/moeda necessária | Média | Usar apenas cotação histórica permitida pela spec; reportar recusa individual sem inventar taxa |
| Viagem não é inferível para todas as datas | Alta | Aplicar somente as datas autorizadas pela RN-004; usar revisão manual nos demais casos, sem presumir contexto |
| Escrita falha ou tenta sobrescrever a entrada | Baixa | Rejeitar caminhos de mesmo arquivo e gravar saída somente após cálculo bem-sucedido; testar preservação da saída em erro |
