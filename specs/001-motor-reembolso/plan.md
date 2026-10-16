# Plano Técnico — Motor de Cálculo de Reembolso

**Versão:** 0.1 · **Status:** proposta · **Baseado na spec:** 0.4 · **Data:** 2026-10-16

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
argumentos CLI → leitura JSON estrita → validação do contrato →
caso de uso de cálculo → serialização do resultado → gravação JSON
```

**Fronteiras:** o adaptador CLI lida com argumentos, data local de referência,
arquivos e códigos de saída. O adaptador de entrada converte JSON em dados
validados; o adaptador de saída converte o resultado em JSON e grava o arquivo.
O núcleo recebe dados validados, a política e `data_calculo`, aplica as regras
da spec e retorna decisões; não lê arquivos, não consulta o relógio e não
escreve no terminal. Isso permite testar regras sem I/O e sem depender da data
real durante os testes.

## 3. Modelo de dados

- `InputBatch`: colaborador, período e lista ordenada de despesas validadas.
- `Expense`: ID, data, categoria original e normalizada, descrição, fornecedor,
  `Decimal` do valor e indicador de nota fiscal.
- `ExpenseDecision`: ID, status da spec, valores informado/reembolsável como
  `Decimal` e lista ordenada de motivos (código e descrição).
- `CalculationResult`: versão do schema, `data_calculo`, moeda, dados do lote,
  decisões por despesa e totais aprovados/em revisão.
- Os modelos não fazem leitura/escrita de arquivos. A serialização converte
  valores monetários para strings com duas casas, conforme o contrato.

## 4. Como a política é representada

Os limites e as categorias reconhecidas ficam centralizados num objeto de
política imutável no núcleo (`policy.py`). A política não é configurável pelo
usuário nem lida de arquivo nesta entrega. Alterar a política exige mudança
revisada na spec, registro em `DECISIONS.md`, atualização dos testes e depois do
objeto de política.

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

### DT-003 — Política centralizada e fixa

**Contexto:** há uma única política e nenhuma interface para configurá-la.
**Decisão:** guardar limites/categorias num objeto imutável central no núcleo.
**Alternativa descartada:** arquivo de configuração externo, que exigiria
contrato, parsing e validações adicionais sem requisito de produto.
**Consequência:** alterações de limite são explícitas e testáveis, mas exigem
alteração de código após atualizar spec e decisões.

### DT-004 — Empacotamento e ferramentas de desenvolvimento

**Contexto:** a CLI precisa ser executável pelo nome documentado e reprodutível
em ambiente limpo.
**Decisão:** `pyproject.toml` com layout `src/reembolso`, entry point `reembolso`
e dependências de desenvolvimento opcionais.
**Alternativa descartada:** depender do diretório atual ou de `PYTHONPATH` manual,
por tornar o comando mais frágil no README e nos testes.
**Consequência:** requer instalação editável do projeto no ambiente virtual; o
comando da CLI fica igual ao contrato e à documentação.

## 6. Estratégia de testes

- **Nível:** maioria unitária para regras puras; integração da CLI para leitura,
  validação, escrita, códigos de saída e preservação de arquivos em erro.
- **Cobertura por requisito:** cada RN e cada caso da seção 7 da spec deve
  referenciar ao menos um teste na matriz de `tasks.md`.
- **Casos de borda:** parametrizar fronteiras de nota, prazo, arredondamento,
  duplicidade e limites; testar viagens com uma e várias hospedagens; testar
  lote vazio, JSON inválido, chaves desconhecidas e mesmo arquivo como entrada
  e saída.
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
| Viagem não é inferível para todas as datas | Alta | Aplicar somente as datas autorizadas pela RN-004; usar revisão manual nos demais casos, sem presumir contexto |
| Escrita falha ou tenta sobrescrever a entrada | Baixa | Rejeitar caminhos de mesmo arquivo e gravar saída somente após cálculo bem-sucedido; testar preservação da saída em erro |
