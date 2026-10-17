# Tasks — Motor de Cálculo de Reembolso

> Cada task é pequena o bastante para virar **um commit**. Se você não consegue
> descrever o critério de aceite como "o teste X passa", a task está grande demais.
>
> Marque `[x]` somente depois de todos os critérios de aceite passarem e de
> preencher o commit correspondente. Atualize o estado logo após cada task para
> que a primeira task `[ ]` na ordem abaixo seja sempre o próximo ponto de retomada.
> Os IDs são estáveis e não devem ser renumerados; tasks retiradas não têm seu ID
> reutilizado.

**Formato do commit:** `feat(T-003): <descrição>` · `test(T-003): <descrição>`

## Estado e ordem de execução

**Estado registrado:** nenhuma task está marcada como concluída; retomar por
**T-001**. O checkbox de cada task detalhada abaixo é a fonte única do estado.
Depois de cada commit, registrar seu hash no campo `Commit` da task e marcar
`[x]` apenas quando todos os critérios de aceite estiverem verificados.
Há scaffolding parcial no worktree; a ausência de checks indica que nenhum
critério foi formalmente verificado, não que os arquivos devam ser recriados.
Começar auditando T-001 e registrar o que já satisfaz seus aceites.

Ao interromper uma task ainda incompleta, acrescentar/preencher nela
`**Retomada:**` com critérios já verificados, arquivos tocados, próximo passo
concreto e bloqueios. Ao concluir, registrar hash curto e título do commit em
`**Commit:**`, marcar `[x]` e limpar a nota de retomada.

IDs são mantidos por rastreabilidade; portanto, a ordem de execução abaixo,
e não a ordem numérica dos IDs, define a sequência. Cada dependência aparece
antes da task que a consome.

1. **T-001** — Estrutura e ambiente (sem dependências).
2. **T-002** — Modelos internos (T-001).
3. **T-003** — Parser de despesas e validação do contrato (T-002).
4. **T-004** — Serializador JSON (T-002).
5. **T-005** — Escrita atômica e identidade dos caminhos (T-004).
6. **T-016** — Testes de coerência do período (T-003).
7. **T-021** — Carregamento e validação da política (T-002, T-003).
8. **T-022** — Resolução de regra por centro/categoria (T-021).
9. **T-023** — Carregamento e seleção de cotações (T-002, T-003).
10. **T-024** — Conversão monetária e cotação ausente (T-023).
11. **T-007** — Normalização e validação de categoria (T-022, T-024).
12. **T-011** — Identificação prévia dos dias de viagem (T-007).
13. **T-006** — Validação de valor por item (T-024).
14. **T-008** — Detecção de duplicatas (T-007, T-024).
15. **T-009** — Prazo e data futura (T-003).
16. **T-010** — Exigência de nota fiscal (T-021, T-024).
17. **T-012** — Revisão manual (T-006 a T-011, T-022).
18. **T-013** — Aplicação dos limites (T-012, T-022, T-024).
19. **T-014** — Arredondamento e totais (T-013, T-024).
20. **T-017** — Lote vazio e entrada mínima (T-014).
21. **T-018** — Integração do núcleo com o fixture original (T-006 a T-014,
    T-021 a T-024).
22. **T-026** — Orquestração CLI e captura única da data (T-003 a T-005,
    T-006 a T-014, T-021 a T-024).
23. **T-019** — Integração da CLI via subprocesso (T-026).
24. **T-020** — Preservação da saída em falhas (T-005, T-019).
25. **T-025** — Integração dos dois fixtures do envelope (T-018 a T-020).
26. **T-027** — README e relatório com evidências (T-025).

**T-015 foi retirada** por duplicar testes já atribuídos ao parser, aos
carregadores de configuração e às tasks de I/O/CLI. Seu ID fica reservado para
preservar a rastreabilidade e não deve ser reutilizado.

O roadmap ordena as entregas por dependência; ele não altera a ordem de
aplicação das regras definida na spec. Em particular, a identificação de viagem
de T-011 é uma pré-análise do lote e precisa ocorrer antes das decisões por item.
Os blocos de critérios abaixo estão agrupados por assunto para consulta; para
executar e retomar o trabalho, siga o roadmap acima.

---

## Catálogo detalhado — Fundação

- [x] **T-001** — Criar estrutura do projeto e ambiente instalável
  - **O que faz:** garante a estrutura instalável do projeto: cria ou completa
    `pyproject.toml` com layout `src/reembolso`, entry point
    `reembolso`, dependências de desenvolvimento (`pytest`, `ruff`) e instala o
    pacote em modo editável. Inclui um teste de smoke para que `pytest` não
    retorne código 5 (sem testes coletados).
  - **Atende:** RN-010, DT-004
  - **Aceite:**
    - `reembolso --help` executa sem erro após `pip install -e ".[dev]"`.
    - `test_smoke_importa_pacote` importa o pacote `reembolso` sem exceção.
    - `ruff check .` e `ruff format --check .` passam sem avisos.
  - **Commit:** `5d31ce6 feat(T-001): cria estrutura instalavel e CLI inicial`

- [x] **T-002** — Definir modelos de dados internos
  - **O que faz:** cria as estruturas internas `InputBatch`, `Expense`,
    `Policy`, `ExchangeRates`, `ExpenseDecision` e `CalculationResult` com
    todos os campos descritos no plano técnico. Valores monetários são
    `Decimal`; `valor_informado` pode ser nulo quando faltar cotação; nenhum
    modelo realiza I/O.
  - **Atende:** DT-001, DT-002, contrato de entrada/saída da spec
  - **Aceite:**
    - `test_models_instantiation` cria instâncias de cada modelo com valores
      válidos e verifica que campos monetários são `Decimal`, não `float`.
  - **Commit:** `6b3c49e feat(T-002): define modelos internos`

- [x] **T-003** — Implementar parser e validador de entrada JSON
  - **O que faz:** lê o JSON de despesas e valida estritamente o contrato
    (campos obrigatórios, `moeda` opcional com default `BRL`, tipos, formatos
    de data, IDs únicos após remoção de espaços
    externos, ausência de propriedades adicionais em qualquer nível). Todos os
    valores numéricos — inteiros e decimais — são lidos como `Decimal`;
    constantes não finitas (`Infinity`, `NaN`) são rejeitadas. Retorna
    `InputBatch` ou levanta erro estrutural que interrompe o lote.
  - **Atende:** contrato de entrada seção 4, RN-010, RN-011, DT-002,
    FURO-015
  - **Aceite:**
    - `test_parser_valido` aceita `despesas-exemplo.json` sem erro.
    - `test_parser_moeda_ausente_default_brl` atribui `BRL` quando o campo não
      é fornecido.
    - `test_parser_moeda_estrangeira` aceita código com formato válido mesmo
      sem catálogo ISO e preserva valor como `Decimal`.
    - `test_parser_inteiro_vira_decimal` valor JSON `100` (inteiro) é lido
      como `Decimal("100")`, não `int`.
    - `test_parser_campo_ausente` rejeita JSON sem `colaborador.id`.
    - `test_parser_objetos_com_campos_ausentes_ou_extras` verifica as chaves
      exatas do objeto raiz e dos objetos `colaborador`, `periodo` e despesa.
    - `test_parser_rejeita_chave_json_repetida` rejeita propriedade repetida em
      qualquer nível do JSON.
    - `test_parser_propriedade_extra_raiz` rejeita JSON com campo extra na raiz.
    - `test_parser_propriedade_extra_colaborador` rejeita campo extra em
      `colaborador`.
    - `test_parser_propriedade_extra_periodo` rejeita campo extra em `periodo`.
    - `test_parser_propriedade_extra_despesa` rejeita campo extra em um item de
      `despesas`.
    - `test_parser_id_repetido` rejeita IDs `"d-001"` e `" d-001 "` como
      duplicados após remoção de espaços.
    - `test_parser_data_invalida` rejeita `"2026-02-30"`.
    - `test_parser_valor_nao_finito` rejeita `Infinity` em `valor`.
    - `test_parser_decimal_preservado` verifica que `54.90` e `54.9` são ambos
      `Decimal` e numericamente iguais.
  - **Commit:** `3609a80 test(T-003): valida contrato estrito de despesas`

- [x] **T-004** — Implementar serializador de saída JSON
  - **O que faz:** converte `CalculationResult` em texto JSON UTF-8, sem acesso
    ao sistema de arquivos. Serializa valores `Decimal` já arredondados como
    strings com exatamente duas casas decimais (ex: `Decimal("33.33")` →
    `"33.33"`). Não aplica arredondamento; apenas formata. Preserva
    `valor_original`, serializa `moeda_original`, permite `valor_informado: null`
    e emite schema `"2.0"` e moeda `"BRL"`.
  - **Atende:** contrato de saída seção 4, FURO-011, ENV-009
  - **Aceite:**
    - `test_serializador_decimal_ja_arredondado` verifica que
      `Decimal("33.33")` serializa como `"33.33"` e `Decimal("0.00")` como
      `"0.00"`.
    - `test_serializador_versao_schema` verifica que `versao_schema` é `"2.0"`.
    - `test_serializador_moeda` verifica que `moeda` é `"BRL"`.
    - `test_serializador_preserva_valor_e_moeda_originais` verifica os campos
      monetários de origem.
    - `test_serializador_valor_informado_nulo` verifica `null` sem cotação.
    - `test_serializador_lote_vazio` verifica saída com `despesas: []` e ambos
      os totais como `"0.00"`.
    - `test_serializador_campos_exatos` verifica as chaves definidas para raiz,
      totais, despesa e motivo.
    - `test_serializador_preserva_ordem_entrada` a lista `despesas` na saída
      mantém a ordem dos itens de `CalculationResult`.
  - **Commit:** `591b737 feat(T-004): serializa resultado JSON`

- [x] **T-005** — Implementar escrita atômica e validação de caminhos
  - **O que faz:** implementa o adaptador de arquivo de saída sem orquestrar a
    CLI. Compara os caminhos de despesas, política, câmbio e saída usando
    caminhos resolvidos e normalizados, verificando também identidade de
    arquivos existentes. Grava o JSON já serializado em arquivo temporário
    exclusivo no mesmo diretório do destino e publica-o com `os.replace`
    somente após escrita bem-sucedida.
  - **Atende:** RN-010, DT-001, DT-006, FURO-016
  - **Aceite:**
    - `test_io_rejeita_caminhos_equivalentes` rejeita dois caminhos para o
      mesmo arquivo, incluindo grafias distintas e aliases existentes.
    - `test_io_grava_substituicao_atomica` substitui a saída somente depois de
      o conteúdo completo estar escrito.
    - `test_io_remove_temporario_apos_falha` remove o temporário quando a
      escrita ou a substituição falha, sem mascarar o erro original.
  - **Commit:** `8b2535b feat(T-005): implementa escrita atomica e caminhos distintos`

---

## Catálogo detalhado — Regras de negócio

- [ ] **T-006** — Implementar validação de valor por item (RN-008)
  - **O que faz:** aplica o passo 3 da ordem de aplicação. Recusa por item:
    valor zero (`valor_zero_invalido`), valor negativo
    (`valor_negativo_fora_escopo`) e valor positivo que arredondado para duas
    casas resulte em R$ 0,00 (`valor_inferior_ao_centavo`). A recusa encerra a
    avaliação daquele item (FURO-013); não impede avaliação das demais despesas.
  - **Atende:** RN-008, AMB-009, AMB-010, FURO-012, FURO-013
  - **Aceite:**
    - `test_rn008_valor_zero` recusa `0` com `valor_zero_invalido`.
    - `test_rn008_valor_negativo` recusa d-009 (`-45.00`) com
      `valor_negativo_fora_escopo`; demais despesas do lote não são afetadas.
    - `test_rn008_valor_subcentavo_0_004` recusa `0.004` com
      `valor_inferior_ao_centavo`.
    - `test_rn008_valor_subcentavo_fronteira_0_005` aceita `0.005` (arredonda
      para `0.01`); não recusa por subcentavo.
    - `test_rn008_recusa_encerra_item` confirma que uma recusa neste passo não
      avalia regras posteriores para aquela despesa, mas o lote continua.
  - **Commit:**

- [ ] **T-007** — Implementar normalização e validação de categoria (RN-007)
  - **O que faz:** aplica o passo 4 da ordem de aplicação. Remove espaços
    externos e converte para minúsculas; consulta a política aplicável por
    centro/categoria e recusa categoria sem regra específica nem padrão com
    `categoria_fora_politica`.
  - **Atende:** RN-007, RN-012, AMB-007, ENV-001, FURO-013
  - **Aceite:**
    - `test_rn007_categoria_maiuscula` `"ALIMENTACAO"` normaliza para
      `alimentacao`.
    - `test_rn007_categoria_com_espacos` `" hospedagem "` normaliza para
      `hospedagem`.
    - `test_rn007_categoria_fora_politica` d-005 (`"coworking"`) recusada com
      `categoria_fora_politica`.
    - `test_rn007_categoria_especifica_por_centro` reconhece `representacao`
      no `CC-COMERCIAL`.
    - `test_rn007_representacao_sem_regra` recusa `representacao` em centro
      sem regra específica nem padrão.
    - `test_rn007_motivo_legivel` `descricao` informa que a categoria está fora
      da política.
    - `test_rn007_recusa_encerra_item` categoria desconhecida com valor de
      R$ 100,00 e sem nota produz somente `categoria_fora_politica`; a regra de
      nota fiscal não é avaliada para esse item, e o lote continua.
  - **Commit:**

- [ ] **T-008** — Implementar detecção de duplicatas (RN-006)
  - **O que faz:** aplica o passo 5 da ordem de aplicação. Compara categoria
    normalizada, data, valor decimal original **numericamente**, moeda original,
    descrição e fornecedor exatamente como recebidos. Mantém a
    primeira ocorrência; recusa posteriores com `duplicata`. A recusa encerra
    o item (FURO-013).
  - **Atende:** RN-006, AMB-006, ENV-008, FURO-013, FURO-014
  - **Aceite:**
    - `test_rn006_duplicata_basica` mantém d-006 e recusa d-007.
    - `test_rn006_valores_numericamente_iguais` `54.90` e `54.9` são duplicatas
      quando demais campos são iguais.
    - `test_rn006_valores_distintos_mesmos_centavos` `33.331` e `33.334` não
      são duplicatas.
    - `test_rn006_moedas_diferentes_nao_sao_duplicatas` preserva lançamentos
      em moedas originais diferentes, mesmo com equivalentes BRL iguais.
    - `test_rn006_fornecedor_case_sensitive` fornecedores com caixa diferente
      não geram duplicata.
    - `test_rn006_recusa_encerra_item` item recusado como duplicata não avalia
      regras posteriores.
  - **Commit:**

- [ ] **T-009** — Implementar prazo de 90 dias e data futura (RN-005)
  - **O que faz:** aplica o passo 6 da ordem de aplicação. Compara a data de
    cada despesa com `data_calculo`. Recusa data futura (`data_futura`) e
    despesa com mais de 90 dias corridos (`prazo_excedido`). Exatamente 90 dias
    é elegível. A recusa encerra o item (FURO-013).
  - **Atende:** RN-005, AMB-005, FURO-013
  - **Aceite:**
    - `test_rn005_prazo_exato_90_dias` despesa exatamente 90 dias antes de
      `data_calculo` passa.
    - `test_rn005_prazo_91_dias` despesa com 91 dias recusada com
      `prazo_excedido`.
    - `test_rn005_data_hoje` despesa com data igual a `data_calculo` é elegível.
    - `test_rn005_data_futura` despesa com data posterior a `data_calculo`
      recusada com `data_futura`.
    - `test_rn005_d008_excede_prazo` d-008 (`2026-04-15`) recusada com
      `data_calculo` `2026-07-31` (107 dias).
  - **Commit:**

- [ ] **T-010** — Implementar exigência de nota fiscal (RN-003)
  - **O que faz:** aplica o passo 7 da ordem de aplicação. Recusa despesa cujo
    valor convertido em BRL antes de arredondar atinja o limite de nota fiscal
    carregado da política, sem nota fiscal (`nota_fiscal_ausente`). A
    recusa é integral e encerra o item (FURO-013).
  - **Atende:** RN-003, RN-013, AMB-003, ENV-006, FURO-013
  - **Aceite:**
    - `test_rn003_exato_100_sem_nota` R$ 100,00 sem nota → recusada (d-003).
    - `test_rn003_acima_100_sem_nota` R$ 100,01 sem nota → recusada (d-004).
    - `test_rn003_abaixo_100_sem_nota` R$ 99,99 sem nota → não recusada por
      esta regra.
    - `test_rn003_exato_100_com_nota` R$ 100,00 com nota → não recusada por
      esta regra.
    - `test_rn003_conversao_antes_do_limite` usa o equivalente BRL para decidir
      se a nota é obrigatória.
    - `test_rn003_recusa_encerra_item` recusa por nota não avalia regras
      posteriores para aquela despesa.
  - **Commit:**

- [ ] **T-011** — Implementar identificação de dias de viagem (RN-004 — passo 2)
  - **O que faz:** aplica o passo 2 da ordem de aplicação, **antes** de
    qualquer recusa por item. Percorre todas as despesas com categoria
    `hospedagem`, data válida e valor original positivo, mesmo quando a
    categoria não tem regra aplicável na política; calcula o dia calendário
    seguinte como data de viagem. Datas repetidas geram um único dia. O
    conjunto de datas de viagem é fixo para o lote inteiro, mesmo que a
    hospedagem seja depois recusada por categoria sem política, duplicidade,
    prazo, cotação ausente ou falta de nota.
  - **Atende:** RN-004, AMB-004, AMB-021, ENV-018, FURO-001, FURO-002
  - **Aceite:**
    - `test_rn004_hospedagem_gera_dia_seguinte` hospedagem em `2026-07-14`
      gera dia de viagem `2026-07-15`.
    - `test_rn004_duas_hospedagens_geram_dois_dias` d-010 (`2026-07-14`) e
      d-013 (`2026-07-22`) geram `{2026-07-15, 2026-07-23}`.
    - `test_rn004_hospedagem_sem_nota_ainda_gera_dia` d-013 (recusada por
      nota) produz `2026-07-23` no conjunto de dias de viagem.
    - `test_rn004_hospedagem_sem_regra_ativa_dia_viagem` hospedagem sem regra
      aplicável é recusada por categoria, mas ainda gera o dia seguinte.
    - `test_rn004_sem_hospedagem_conjunto_vazio` lote sem hospedagem produz
      conjunto vazio.
    - `test_rn004_datas_repetidas_dia_unico` duas hospedagens na mesma data
      geram apenas um dia de viagem; sem acúmulo de limite.
  - **Commit:**

- [ ] **T-012** — Implementar revisão manual (RN-004 — passo 8)
  - **O que faz:** aplica o passo 8 da ordem de aplicação. Despesas de
    categoria `hospedagem` recebem `revisao_manual` com motivo
    `revisao_manual_viagem` (descrição: diárias indetermináveis) quando a regra
    aplicável tem limite positivo. Despesas elegíveis de outras categorias em
    datas **fora** do conjunto de dias de viagem recebem o mesmo status
    (descrição: data não identificada como dia de viagem). Recusas anteriores
    prevalecem.
  - **Atende:** RN-004, RN-012, AMB-004, AMB-008, ENV-010, FURO-010
  - **Aceite:**
    - `test_rn004_hospedagem_revisao_manual` despesa de hospedagem com regra
      aplicável de limite positivo → `revisao_manual` com
      `revisao_manual_viagem`.
    - `test_rn012_limite_zero_recusa_antes_de_revisao` limite zero recusa antes
      da revisão manual, com ou sem marcador explícito.
    - `test_rn004_descricao_distingue_causa` hospedagem com regra aplicável de
      limite positivo difere na `descricao` de d-012 (data não identificada).
    - `test_rn004_data_nao_identificada_revisao_manual` d-012 (`2026-07-18`)
      com hospedagens em d-010 e d-013 → `revisao_manual`.
    - `test_rn004_recusa_prevalece_sobre_revisao_manual` despesa recusada por
      prazo em lote com hospedagem permanece `recusada`.
    - `test_rn004_sem_hospedagem_sem_revisao_manual` lote sem hospedagem não
      gera `revisao_manual` por motivo de viagem.
  - **Commit:**

- [ ] **T-013** — Implementar aplicação de teto por despesa (RN-001, RN-002, RN-004 — passo 9)
  - **O que faz:** aplica o passo 9 da ordem de aplicação usando limites
    fornecidos pela política; os testes unitários de RN-001 usam uma política
    de teste com limites R$ 60/R$ 80, não constantes no código. Para despesas
    elegíveis (não recusadas e não em revisão manual), seleciona teto específico
    do centro de custo com fallback por categoria à política padrão. Regras com
    limite zero já foram recusadas por T-012. Se a data estiver no conjunto de
    dias de viagem, aumenta o teto configurado — uma única vez, sem acúmulo.
    Reembolsa no máximo o equivalente BRL.
    Registra todos os motivos aplicáveis na ordem de aplicação: `dentro_do_limite`
    quando o valor não atinge o teto; `limite_aplicado` quando o teto corta;
    `limite_viagem_aplicado` quando o teto ampliado é utilizado (combinado com
    `dentro_do_limite` ou `limite_aplicado` conforme o caso).
  - **Atende:** RN-001, RN-002, RN-004, RN-012, AMB-001, AMB-002, ENV-001,
    ENV-010, FURO-003, FURO-005, FURO-006
  - **Aceite:**
    - `test_rn001_alimentacao_abaixo_teto` com regra de teste de R$ 60,
      R$ 38,00 → R$ 38,00, motivo
      `dentro_do_limite`.
    - `test_rn001_alimentacao_acima_teto` com regra de teste de R$ 60,
      R$ 72,50 → R$ 60,00, motivo
      `limite_aplicado`.
    - `test_rn001_transporte_abaixo_teto` com regra de teste de R$ 80,
      R$ 75,00 → R$ 75,00, motivo
      `dentro_do_limite`.
    - `test_rn001_transporte_acima_teto` com regra de teste de R$ 80, R$ 100,00
      com nota → R$ 80,00, motivo
      `limite_aplicado`.
    - `test_rn004_viagem_abaixo_teto_ampliado` d-011 (R$ 33,333 em dia de
      viagem, teto R$ 90) → motivos `[limite_viagem_aplicado, dentro_do_limite]`.
    - `test_rn004_viagem_acima_teto_ampliado` alimentação R$ 100,00 com nota
      em dia de viagem → R$ 90,00, motivos `[limite_viagem_aplicado,
      limite_aplicado]`.
    - `test_rn004_duas_despesas_mesmo_dia_viagem` duas refeições em
      `2026-07-15` recebem teto R$ 90,00 individualmente, sem agregação.
    - `test_rn006_motivos_nao_vazios` toda despesa tem `motivos` não vazio.
  - **Commit:**

- [ ] **T-014** — Implementar arredondamento monetário e cálculo de totais (RN-009 — passo 10)
  - **O que faz:** aplica o passo 10. Converte antes de arredondar e arredonda
    cada valor BRL por despesa para duas casas (terceiro algarismo 0–4 para
    baixo; 5–9 para cima)
    e entrega valores `Decimal` já arredondados ao serializador. Calcula
    `totais.valor_reembolsavel` e `totais.valor_em_revisao` somando os valores
    arredondados de cada despesa. Esta task é a única responsável pelo
    arredondamento; T-004 apenas formata strings.
  - **Atende:** RN-009, AMB-010
  - **Aceite:**
    - `test_rn009_arredondamento_para_baixo` `33.333` arredonda para
      `Decimal("33.33")`.
    - `test_rn009_arredondamento_para_cima` `33.335` arredonda para
      `Decimal("33.34")`.
    - `test_rn009_total_soma_arredondados` total é a soma dos `Decimal`
      arredondados por despesa, não dos valores brutos.
    - `test_rn009_total_em_revisao` `totais.valor_em_revisao` soma o
      `valor_informado` arredondado das despesas em `revisao_manual`.
  - **Commit:**

---

## Catálogo detalhado — Validação complementar e lote vazio

- [x] **T-016** — Validação de competência e período (RN-011)
  - **O que faz:** testa as validações de coerência entre `competencia`,
    `periodo.inicio` e `periodo.fim` definidas em RN-011.
  - **Atende:** RN-011, FURO-007, FURO-008
  - **Aceite:**
    - `test_rn011_inicio_fora_competencia` competência `2026-07`, início
      `2026-06-30` → rejeitado.
    - `test_rn011_fim_anterior_ao_inicio` `fim < inicio` → rejeitado.
    - `test_rn011_fim_mes_posterior_aceito` competência `2026-07`, início
      `2026-07-01`, fim `2026-08-15` → aceito.
    - `test_rn011_inicio_qualquer_dia_mes` início `2026-07-15` com competência
      `2026-07` → aceito.
  - **Commit:** `0b0dfcb test(T-016): cobre coerencia do periodo`

- [ ] **T-017** — Lote vazio e entrada mínima
  - **O que faz:** testa lote com `despesas: []` e lote com uma única despesa
    válida.
  - **Atende:** contrato de saída seção 4, FURO-009
  - **Aceite:**
    - `test_lote_vazio_saida_valida` `despesas: []` → saída com `despesas: []`,
      `totais.valor_reembolsavel: "0.00"` e `totais.valor_em_revisao: "0.00"`.
    - `test_lote_uma_despesa_valida` lote com uma despesa elegível abaixo do
      teto → `status: "reembolsada"`, total correto.
  - **Commit:**

---

## Catálogo detalhado — Integração

- [ ] **T-018** — Integração do núcleo com o lote de exemplo completo
  - **O que faz:** executa o núcleo sobre `despesas-exemplo.json` com data
    `2026-07-31`, política e câmbio explícitos. Verifica os 14 resultados
    contra as regras v4, incluindo limites do `CC-ENG-PLATAFORMA`, categorias
    sem política, hospedagens e totais.
  - **Atende:** todas as RNs (integração)
  - **Aceite:** `test_integracao_lote_completo` verifica:
    - d-001 e d-002 → `revisao_manual` por hospedagem no lote e data fora dos
      dias identificados.
    - d-003 e d-004 → recusadas por `nota_fiscal_ausente`.
    - d-005 → recusada por `categoria_fora_politica`.
    - d-006 → `revisao_manual`; d-007 → recusada como `duplicata`.
    - d-008 → recusada por `prazo_excedido`; d-009 → recusada por
      `valor_negativo_fora_escopo`.
    - d-010 → recusada com `limite_zero_nao_reembolsavel`, mas gera dia de
      viagem 2026-07-15 por ter valor original positivo.
    - d-011 → `reembolsada`, `"33.33"`, motivos
      `[limite_viagem_aplicado, dentro_do_limite]`.
    - d-012 e d-014 → `revisao_manual`.
    - d-013 → recusada por `nota_fiscal_ausente`, mas gera dia de viagem
      2026-07-23.
    - Totais: `valor_reembolsavel: "33.33"` e
      `valor_em_revisao: "273.60"`.
  - **Commit:**

- [ ] **T-019** — Integração CLI via subprocesso
  - **O que faz:** invoca `reembolso calcular --input --output --policy
    --exchange-rates` via
    `subprocess` com arquivo temporário, verifica código de retorno, JSON
    válido na saída e campos obrigatórios do contrato.
  - **Atende:** RN-010, contrato de saída seção 4
  - **Aceite:**
    - `test_cli_integracao_subprocess` invoca a CLI com
      `despesas-exemplo.json`; verifica código 0; carrega a saída e confirma
      `versao_schema: "2.0"`, `moeda: "BRL"` e `data_calculo` no formato
      `AAAA-MM-DD`.
  - **Commit:**

- [ ] **T-020** — Preservação de saída em falha de I/O
  - **O que faz:** simula falha real de gravação (ex: permissão negada no
    diretório de destino ou disco cheio) e confirma que a saída preexistente
    permanece intacta. Valida a estratégia de gravação temporária + substituição
    atômica definida em T-005.
  - **Atende:** RN-010, DT-001
  - **Aceite:**
    - `test_io_preserva_saida_em_falha_gravacao` simula erro ao mover o
      arquivo temporário para o destino; saída preexistente não é alterada.
    - `test_io_preserva_saida_arquivo_entrada_ausente` entrada inexistente →
      saída preexistente inalterada.
    - `test_io_preserva_saida_configuracao_invalida` política/câmbio inválido
      não altera a saída preexistente.
  - **Commit:**

---

## Catálogo detalhado — Política externa, moedas e envelope

> Tasks para os requisitos v4. Numeração continua em T-021.

- [ ] **T-021** — Carregar e validar política externa
  - **O que faz:** lê o arquivo apontado por `--policy`, valida que `versao` é
    uma string não vazia após remover espaços externos (sem restringir seus
    rótulos), vigência, moeda-base,
    tabelas, limites, periodicidades, categorias e propriedades permitidas;
    valida vigência contra `data_calculo`, detecta colisões de centros após
    normalização e cria `Policy` imutável.
  - **Atende:** RN-012, ENV-011, ENV-017
  - **Aceite:**
    - `test_policy_v4_valida` aceita `politica-v4.json`.
    - `test_policy_rejeita_limite_negativo`, `test_policy_rejeita_categoria_vazia`
      e `test_policy_rejeita_propriedade_extra` recusam configuração inválida.
    - `test_policy_rejeita_chave_json_repetida` rejeita propriedade duplicada.
    - `test_policy_rejeita_vigencia_futura` rejeita política ainda não vigente
      em `data_calculo`.
    - `test_policy_rejeita_marcador_com_limite_positivo` rejeita a combinação
      inconsistente.
    - `test_policy_aceita_rotulo_versao_desconhecido` aceita rótulo não vazio
      diferente de `v4` quando o restante satisfaz o schema.
    - `test_policy_rejeita_versao_vazia` rejeita versão vazia ou só com espaços.
    - `test_policy_rejeita_chave_vazia` rejeita chave vazia de centro ou
      categoria após normalização.
    - `test_policy_chaves_centros_colidem` rejeita chaves de centros que
      colidam após normalização.
    - `test_policy_nao_reembolsavel_preservada` preserva a observação do limite
      zero de `CC-ENG-PLATAFORMA`.
  - **Commit:**

- [ ] **T-022** — Resolver limites por centro de custo
  - **O que faz:** implementa a resolução pura de regra: seleciona regra
    específica, fallback padrão por categoria ou política padrão integral para
    centro desconhecido; normaliza centro removendo espaços externos e
    ignorando caixa. Não aplica decisão à despesa: categoria sem regra é
    devolvida como ausência para T-007, e limite zero é tratado por T-012 antes
    da revisão manual.
  - **Atende:** RN-007, RN-012, ENV-001, ENV-010
  - **Aceite:**
    - `test_policy_centro_desconhecido_usa_padrao`.
    - `test_policy_categoria_ausente_usa_padrao`.
    - `test_policy_sem_regra_retorna_ausencia` quando não há regra nem no
      centro nem no padrão.
    - `test_policy_centro_ignora_caixa_e_espacos` resolve códigos normalizados.
  - **Commit:**

- [ ] **T-023** — Carregar e selecionar cotações históricas
  - **O que faz:** valida `cambio.json` e seleciona para cada moeda a data de
    cotação mais recente menor ou igual à data da despesa. Permite taxa explícita
    para `BRL` apenas quando igual a 1. Não consulta a rede.
  - **Atende:** RN-013, ENV-003, ENV-004, ENV-005, ENV-020
  - **Aceite:**
    - `test_exchange_rates_valida_cambio_envelope`.
    - `test_cotacao_exata_usa_fechamento`.
    - `test_cotacao_fim_de_semana_usa_ultima_anterior`.
    - `test_cotacao_nao_usa_data_futura`.
    - `test_moeda_sem_cotacao_retorna_ausencia`.
    - `test_cotacao_nao_consulta_rede`.
    - `test_exchange_rates_rejeita_chave_json_repetida`.
    - `test_exchange_rates_aceita_brl_unitario`.
    - `test_exchange_rates_rejeita_brl_nao_unitario`.
    - `test_exchange_rates_rejeita_schema_ou_taxas_invalidos` cobre campos,
      tipos, datas, códigos e valores fora do contrato.
  - **Commit:**

- [ ] **T-024** — Converter valores para BRL e tratar cotação ausente
  - **O que faz:** converte cada valor para BRL usando `Decimal` e a cotação
    elegível de T-023, sem arredondamento intermediário. Mantém o valor e a
    moeda originais disponíveis para a saída. Sem cotação utilizável, recusa o
    item com `cotacao_indisponivel` e `valor_informado: null`; não implementa
    status nem regras impeditivas distintas da cotação.
  - **Atende:** RN-003, RN-006, RN-009, RN-013, ENV-002, ENV-006, ENV-007,
    ENV-008, ENV-009, ENV-019
  - **Aceite:**
    - `test_conversao_multiplica_decimal_sem_float`.
    - `test_moeda_ausente_equivale_brl`.
    - `test_cotacao_ausente_recusa_item_com_valor_nulo`.
    - `test_conversao_preserva_valor_moeda_originais` mantém os campos de
      origem distintos do equivalente em BRL.
  - **Commit:**

- [ ] **T-025** — Validar a entrega do envelope ponta a ponta
  - **O que faz:** executa CLI e núcleo com os dois arquivos de despesas do
    envelope, política v4 e câmbio versionado; não altera os JSON de despesas
    recebidos. Documentação e relatório pertencem à T-027.
  - **Atende:** RN-010, RN-012, RN-013 e critérios de aceite da spec
  - **Aceite:**
    - `test_envelope_despesas_principais` executa com `data_calculo` em
      `2026-07-31`: e-001 `revisao_manual`, `valor_informado` `"340.00"`; e-002
      `revisao_manual`, `"130.46"`; e-003 `revisao_manual`, `"85.26"`; e-004
      `revisao_manual`, `"178.80"`; e-005 recusada por `nota_fiscal_ausente`,
      `"220.00"`; e-006 recusada por `cotacao_indisponivel`, `null` (GBP não
      consta no fixture); e-007 `revisao_manual`, `"1200.00"`; e-008
      `reembolsada`, `valor_informado` e `valor_reembolsavel` `"95.00"`, pois
      2026-07-23 é dia de viagem e o teto ampliado é R$ 135,00; e-009 recusada
      por `categoria_fora_politica`; e-010 `revisao_manual`, `"88.00"`. Totais:
      aprovado `"95.00"` e em revisão `"2022.52"`.
    - `test_envelope_centro_desconhecido` executa com `data_calculo` em
      `2026-07-31`: f-001 `revisao_manual`, `valor_informado` `"58.00"`; f-002
      `revisao_manual`, `"310.00"`; f-003 recusada por
      `categoria_fora_politica`; f-004 `revisao_manual`, `"65.76"`. As
      revisões usam `revisao_manual_viagem`; a única data de viagem identificada
      é 2026-07-18. Totais: aprovado `"0.00"` e em revisão `"433.76"`.
    - `test_valor_informado_convertido_em_despesa_recusada` confirma que uma
      recusa por categoria ainda informa o equivalente BRL quando há cotação.
    - Ambos os testes verificam ordem, status, valores, códigos de motivo e
      totais; os fixtures originais permanecem inalterados.
  - **Commit:**

- [ ] **T-026** — Integrar a CLI com carregadores e núcleo
  - **O que faz:** implementa o subcomando
    `calcular --input --output --policy --exchange-rates`, conecta os
    adaptadores validados, o núcleo, serializador e gravador de T-005; captura
    a data local uma única vez e injeta `data_calculo`. Não aceita opção
    pública para sobrescrever o relógio.
  - **Atende:** RN-005, RN-010, DT-001, FURO-017, ENV-011
  - **Aceite:**
    - `test_cli_exige_arquivos_policy_e_exchange_rates` rejeita cada argumento
      obrigatório ausente.
    - `test_cli_codigo_zero_com_recusas` retorna código zero para um lote
      estruturalmente válido com despesas recusadas.
    - `test_cli_codigo_nonzero_entrada_invalida` retorna código diferente de
      zero para entrada/configuração inválida.
    - `test_cli_data_calculo_na_saida` verifica data controlada no teste e
      confirma que o relógio é consultado uma única vez.
  - **Commit:**

- [ ] **T-027** — Atualizar instruções e relatório da entrega
  - **O que faz:** atualiza README e relatório para documentar instalação,
    execução com os quatro caminhos obrigatórios, testes e evidências da
    implementação do envelope. Distingue fatos verificados de medições não
    realizadas.
  - **Atende:** RN-010 e requisitos de entrega do envelope
  - **Aceite:**
    - README contém comandos reproduzíveis de instalação, execução e testes.
    - relatório identifica os arquivos tocados, evidencia as verificações
      realmente executadas e não afirma medições não realizadas.
  - **Commit:**

---

## Cobertura

| Regra / Decisão | Task(s) | Teste(s) representativo(s) |
|---|---|---|
| RN-001 | T-013 | `test_rn001_alimentacao_acima_teto`, `test_rn001_transporte_acima_teto` |
| RN-002 | T-013 | `test_rn001_alimentacao_acima_teto` |
| RN-003 | T-010, T-024 | `test_rn003_exato_100_sem_nota`, `test_nota_fiscal_usa_equivalente_brl` |
| RN-004 | T-011, T-012, T-013 | `test_rn004_duas_hospedagens_geram_dois_dias`, `test_rn004_hospedagem_sem_nota_ainda_gera_dia`, `test_rn004_hospedagem_sem_regra_ativa_dia_viagem` |
| RN-005 | T-009 | `test_rn005_prazo_exato_90_dias`, `test_rn005_prazo_91_dias` |
| RN-006 | T-008, T-024 | `test_rn006_duplicata_basica`, `test_rn006_moedas_diferentes_nao_sao_duplicatas` |
| RN-007 | T-007, T-022 | `test_rn007_categoria_maiuscula`, `test_policy_sem_regra_recusa_categoria` |
| RN-008 | T-006 | `test_rn008_valor_negativo`, `test_rn008_valor_subcentavo_0_004` |
| RN-009 | T-014, T-024 | `test_rn009_arredondamento_para_cima`, `test_conversao_multiplica_decimal_sem_float` |
| RN-010 | T-001, T-005, T-019, T-020, T-025, T-026 | `test_cli_integracao_subprocess` |
| RN-011 | T-003, T-016 | `test_rn011_inicio_fora_competencia`, `test_rn011_fim_mes_posterior_aceito` |
| RN-012 | T-021, T-022, T-012 | `test_policy_centro_desconhecido_usa_padrao`, `test_rn012_limite_zero_recusa_antes_de_revisao` |
| RN-013 | T-023, T-024 | `test_cotacao_fim_de_semana_usa_ultima_anterior`, `test_cotacao_ausente_recusa_item_com_valor_nulo` |
| AMB-001 | T-013 | `test_rn001_alimentacao_abaixo_teto` |
| AMB-002 | T-013 | `test_rn001_alimentacao_acima_teto` |
| AMB-003 | T-010 | `test_rn003_exato_100_sem_nota` |
| AMB-004 | T-011, T-012 | `test_rn004_hospedagem_gera_dia_seguinte` |
| AMB-005 | T-009 | `test_rn005_prazo_exato_90_dias` |
| AMB-006 | T-008 | `test_rn006_valores_numericamente_iguais` |
| AMB-007 | T-007 | `test_rn007_categoria_maiuscula` |
| AMB-008 | T-012 | `test_rn004_hospedagem_revisao_manual` |
| AMB-009 | T-006 | `test_rn008_valor_negativo` |
| AMB-010 | T-006, T-014 | `test_rn008_valor_subcentavo_0_004`, `test_rn009_arredondamento_para_cima` |
| AMB-020 | T-021 | `test_policy_aceita_rotulo_versao_desconhecido` |
| AMB-021 | T-011 | `test_rn004_hospedagem_sem_regra_ativa_dia_viagem` |
| AMB-022 | T-024 | `test_valor_informado_convertido_em_despesa_recusada` |
| AMB-023 | T-023 | `test_exchange_rates_aceita_brl_unitario`, `test_exchange_rates_rejeita_brl_nao_unitario` |
| FURO-001 | T-011 | `test_rn004_hospedagem_sem_nota_ainda_gera_dia` |
| FURO-002 | T-011 | `test_rn004_duas_hospedagens_geram_dois_dias` |
| FURO-003 | T-013 | `test_rn004_duas_despesas_mesmo_dia_viagem` |
| FURO-005 | T-013 | `test_rn004_viagem_abaixo_teto_ampliado` |
| FURO-006 | T-013 | `test_rn006_motivos_nao_vazios` |
| FURO-007 | T-016 | `test_rn011_fim_anterior_ao_inicio` |
| FURO-008 | T-016 | `test_rn011_inicio_fora_competencia` |
| FURO-009 | T-017 | `test_lote_vazio_saida_valida` |
| FURO-010 | T-012 | `test_rn004_descricao_distingue_causa` |
| FURO-011 | T-004 | `test_serializador_versao_schema` |
| FURO-012 | T-006 | `test_rn008_valor_subcentavo_0_004`, `test_rn008_valor_subcentavo_fronteira_0_005` |
| FURO-013 | T-006, T-007, T-008, T-009, T-010 | `test_rn008_recusa_encerra_item`, `test_rn007_recusa_encerra_item`, `test_rn006_recusa_encerra_item` |
| FURO-014 | T-008 | `test_rn006_valores_numericamente_iguais`, `test_rn006_valores_distintos_mesmos_centavos` |
| FURO-015 | T-003 | `test_parser_propriedade_extra_raiz`, `test_parser_propriedade_extra_periodo` |
| FURO-016 | T-005 | `test_io_rejeita_caminhos_equivalentes` |
| FURO-017 | T-026 | `test_cli_data_calculo_na_saida` |
| ENV-001 | T-022 | `test_policy_centro_desconhecido_usa_padrao`, `test_policy_categoria_ausente_usa_padrao` |
| ENV-002 | T-003, T-024 | `test_moeda_ausente_equivale_brl` |
| ENV-003, ENV-004 | T-023 | `test_cotacao_fim_de_semana_usa_ultima_anterior`, `test_cotacao_nao_usa_data_futura` |
| ENV-005 | T-023, T-025 | `test_envelope_despesas_principais` confirma recusa de GBP sem taxa no fixture |
| ENV-006, ENV-007 | T-010, T-014, T-024 | `test_nota_fiscal_usa_equivalente_brl`, `test_conversao_multiplica_decimal_sem_float` |
| ENV-008 | T-008, T-024 | `test_rn006_moedas_diferentes_nao_sao_duplicatas` |
| ENV-009 | T-004, T-024 | `test_serializador_preserva_valor_e_moeda_originais`, `test_serializador_valor_informado_nulo` |
| ENV-010, ENV-016 | T-021, T-022, T-012 | `test_rn012_limite_zero_recusa_antes_de_revisao`, `test_policy_rejeita_marcador_com_limite_positivo` |
| ENV-011 | T-026, T-019, T-025 | `test_cli_exige_arquivos_policy_e_exchange_rates` |
| ENV-012 | Fora de escopo (opcional) | Não implementado nesta entrega |
| ENV-017 | T-021 | `test_policy_aceita_rotulo_versao_desconhecido` |
| ENV-018 | T-011 | `test_rn004_hospedagem_sem_regra_ativa_dia_viagem` |
| ENV-019 | T-025 | `test_valor_informado_convertido_em_despesa_recusada` |
| ENV-020 | T-023 | `test_exchange_rates_aceita_brl_unitario`, `test_exchange_rates_rejeita_brl_nao_unitario` |
