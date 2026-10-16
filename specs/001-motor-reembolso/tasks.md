# Tasks — Motor de Cálculo de Reembolso

> Cada task é pequena o bastante para virar **um commit**. Se você não consegue
> descrever o critério de aceite como "o teste X passa", a task está grande demais.
>
> Marque `[x]` conforme conclui — ao longo do caminho, não tudo no fim. O histórico
> de quando cada task foi marcada é lido na correção.

**Formato do commit:** `feat(T-003): <descrição>` · `test(T-003): <descrição>`

---

## Fase 1 — Fundação

- [ ] **T-001** — Criar estrutura do projeto e ambiente instalável
  - **O que faz:** cria `pyproject.toml` com layout `src/reembolso`, entry point
    `reembolso`, dependências de desenvolvimento (`pytest`, `ruff`) e instala o
    pacote em modo editável. Inclui um teste de smoke para que `pytest` não
    retorne código 5 (sem testes coletados).
  - **Atende:** RN-010, DT-004
  - **Aceite:**
    - `reembolso --help` executa sem erro após `pip install -e ".[dev]"`.
    - `test_smoke_importa_pacote` importa o pacote `reembolso` sem exceção.
    - `ruff check .` e `ruff format --check .` passam sem avisos.
  - **Commit:**

- [ ] **T-002** — Definir modelos de dados internos
  - **O que faz:** cria as estruturas internas `InputBatch`, `Expense`,
    `ExpenseDecision` e `CalculationResult` com todos os campos descritos no
    plano técnico. Valores monetários são `Decimal`; nenhum modelo realiza I/O.
  - **Atende:** DT-001, DT-002, contrato de entrada/saída da spec
  - **Aceite:**
    - `test_models_instantiation` cria instâncias de cada modelo com valores
      válidos e verifica que campos monetários são `Decimal`, não `float`.
  - **Commit:**

- [ ] **T-003** — Implementar parser e validador de entrada JSON
  - **O que faz:** lê o arquivo JSON e valida estritamente o contrato (campos
    obrigatórios, tipos, formatos de data, IDs únicos após remoção de espaços
    externos, ausência de propriedades adicionais em qualquer nível). Todos os
    valores numéricos — inteiros e decimais — são lidos como `Decimal`;
    constantes não finitas (`Infinity`, `NaN`) são rejeitadas. Retorna
    `InputBatch` ou levanta erro estrutural que interrompe o lote.
  - **Atende:** contrato de entrada seção 4, RN-010, RN-011, DT-002,
    FURO-015
  - **Aceite:**
    - `test_parser_valido` aceita o arquivo `despesas-exemplo.json` sem erro.
    - `test_parser_inteiro_vira_decimal` valor JSON `100` (inteiro) é lido
      como `Decimal("100")`, não `int`.
    - `test_parser_campo_ausente` rejeita JSON sem `colaborador.id`.
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
  - **Commit:**

- [ ] **T-004** — Implementar serializador de saída JSON
  - **O que faz:** converte `CalculationResult` em texto JSON UTF-8, sem acesso
    ao sistema de arquivos. Serializa valores `Decimal` já arredondados como
    strings com exatamente duas casas decimais (ex: `Decimal("33.33")` →
    `"33.33"`). Não aplica arredondamento; apenas formata. Os campos fixos
    `versao_schema` e `moeda` recebem `"1.0"` e `"BRL"`.
  - **Atende:** contrato de saída seção 4, FURO-011
  - **Aceite:**
    - `test_serializador_decimal_ja_arredondado` verifica que
      `Decimal("33.33")` serializa como `"33.33"` e `Decimal("0.00")` como
      `"0.00"`.
    - `test_serializador_versao_schema` verifica que `versao_schema` é `"1.0"`.
    - `test_serializador_moeda` verifica que `moeda` é `"BRL"`.
    - `test_serializador_lote_vazio` verifica saída com `despesas: []` e ambos
      os totais como `"0.00"`.
    - `test_serializador_preserva_ordem_entrada` a lista `despesas` na saída
      mantém a ordem dos itens de `CalculationResult`.
  - **Commit:**

- [ ] **T-005** — Implementar CLI e integração de I/O
  - **O que faz:** implementa o subcomando `calcular --input --output`. Captura
    a data local **uma única vez** no início da execução e injeta-a em todo o
    lote como `data_calculo` (FURO-017). É responsável pelas operações de
    arquivo: rejeita `--input` e `--output` apontando para o mesmo arquivo
    (FURO-016), grava o texto do serializador em arquivo temporário no mesmo
    diretório do destino e substitui o destino somente após cálculo bem-sucedido.
    Preserva arquivo de saída preexistente em qualquer erro.
  - **Atende:** RN-010, RN-005 (captura única da data), DT-001, FURO-016,
    FURO-017
  - **Aceite:**
    - `test_cli_codigo_zero_com_recusas` código de saída 0 mesmo com despesas
      recusadas.
    - `test_cli_codigo_nonzero_entrada_invalida` código != 0 para JSON
      malformado.
    - `test_cli_rejeita_mesmo_arquivo` `--input x.json --output x.json`
      encerra com código != 0 sem alterar o arquivo.
    - `test_cli_data_calculo_na_saida` `data_calculo` na saída corresponde à
      data fornecida por um relógio controlado no teste; a CLI pública não
      recebe opção para sobrescrever a data.
  - **Commit:**

---

## Fase 2 — Regras de negócio

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
    externos e converte para minúsculas; recusa categoria não reconhecida com
    `categoria_fora_politica`. Categorias reconhecidas: `alimentacao`,
    `transporte_urbano`, `hospedagem`.
  - **Atende:** RN-007, AMB-007, FURO-013
  - **Aceite:**
    - `test_rn007_categoria_maiuscula` `"ALIMENTACAO"` normaliza para
      `alimentacao`.
    - `test_rn007_categoria_com_espacos` `" hospedagem "` normaliza para
      `hospedagem`.
    - `test_rn007_categoria_fora_politica` d-005 (`"coworking"`) recusada com
      `categoria_fora_politica`.
    - `test_rn007_motivo_legivel` `descricao` informa que a categoria está fora
      da política.
    - `test_rn007_recusa_encerra_item` categoria desconhecida com valor de
      R$ 100,00 e sem nota produz somente `categoria_fora_politica`; a regra de
      nota fiscal não é avaliada para esse item, e o lote continua.
  - **Commit:**

- [ ] **T-008** — Implementar detecção de duplicatas (RN-006)
  - **O que faz:** aplica o passo 5 da ordem de aplicação. Compara categoria
    normalizada, data, valor decimal **numericamente** antes de arredondar
    (FURO-014), descrição e fornecedor exatamente como recebidos. Mantém a
    primeira ocorrência; recusa posteriores com `duplicata`. A recusa encerra
    o item (FURO-013).
  - **Atende:** RN-006, AMB-006, FURO-013, FURO-014
  - **Aceite:**
    - `test_rn006_duplicata_basica` mantém d-006 e recusa d-007.
    - `test_rn006_valores_numericamente_iguais` `54.90` e `54.9` são duplicatas
      quando demais campos são iguais.
    - `test_rn006_valores_distintos_mesmos_centavos` `33.331` e `33.334` não
      são duplicatas.
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
  - **O que faz:** aplica o passo 7 da ordem de aplicação. Recusa despesa com
    valor original ≥ R$ 100,00 sem nota fiscal (`nota_fiscal_ausente`). A
    recusa é integral e encerra o item (FURO-013).
  - **Atende:** RN-003, AMB-003, FURO-013
  - **Aceite:**
    - `test_rn003_exato_100_sem_nota` R$ 100,00 sem nota → recusada (d-003).
    - `test_rn003_acima_100_sem_nota` R$ 100,01 sem nota → recusada (d-004).
    - `test_rn003_abaixo_100_sem_nota` R$ 99,99 sem nota → não recusada por
      esta regra.
    - `test_rn003_exato_100_com_nota` R$ 100,00 com nota → não recusada por
      esta regra.
    - `test_rn003_recusa_encerra_item` recusa por nota não avalia regras
      posteriores para aquela despesa.
  - **Commit:**

- [ ] **T-011** — Implementar identificação de dias de viagem (RN-004 — passo 2)
  - **O que faz:** aplica o passo 2 da ordem de aplicação, **antes** de
    qualquer recusa por item. Percorre todas as despesas com categoria
    `hospedagem`, data válida e valor positivo; calcula o dia calendário
    seguinte como data de viagem. Datas repetidas geram um único dia. O
    conjunto de datas de viagem é fixo para o lote inteiro, mesmo que a
    hospedagem seja depois recusada por duplicidade, prazo ou falta de nota
    (FURO-001).
  - **Atende:** RN-004, AMB-004, FURO-001, FURO-002
  - **Aceite:**
    - `test_rn004_hospedagem_gera_dia_seguinte` hospedagem em `2026-07-14`
      gera dia de viagem `2026-07-15`.
    - `test_rn004_duas_hospedagens_geram_dois_dias` d-010 (`2026-07-14`) e
      d-013 (`2026-07-22`) geram `{2026-07-15, 2026-07-23}`.
    - `test_rn004_hospedagem_sem_nota_ainda_gera_dia` d-013 (recusada por
      nota) produz `2026-07-23` no conjunto de dias de viagem.
    - `test_rn004_sem_hospedagem_conjunto_vazio` lote sem hospedagem produz
      conjunto vazio.
    - `test_rn004_datas_repetidas_dia_unico` duas hospedagens na mesma data
      geram apenas um dia de viagem; sem acúmulo de limite.
  - **Commit:**

- [ ] **T-012** — Implementar revisão manual (RN-004 — passo 8)
  - **O que faz:** aplica o passo 8 da ordem de aplicação. Despesas de
    categoria `hospedagem` recebem `revisao_manual` com motivo
    `revisao_manual_viagem` (descrição: diárias indetermináveis). Despesas
    elegíveis de outras categorias em datas **fora** do conjunto de dias de
    viagem recebem o mesmo status (descrição: data não identificada como dia
    de viagem). Recusas dos passos 3–7 prevalecem e não são substituídas.
  - **Atende:** RN-004, AMB-004, AMB-008, FURO-010
  - **Aceite:**
    - `test_rn004_hospedagem_revisao_manual` d-010 → `revisao_manual` com
      `revisao_manual_viagem`.
    - `test_rn004_descricao_distingue_causa` `descricao` de d-010 (hospedagem)
      difere da `descricao` de d-012 (data não identificada).
    - `test_rn004_data_nao_identificada_revisao_manual` d-012 (`2026-07-18`)
      com hospedagens em d-010 e d-013 → `revisao_manual`.
    - `test_rn004_recusa_prevalece_sobre_revisao_manual` despesa recusada por
      prazo em lote com hospedagem permanece `recusada`.
    - `test_rn004_sem_hospedagem_sem_revisao_manual` lote sem hospedagem não
      gera `revisao_manual` por motivo de viagem.
  - **Commit:**

- [ ] **T-013** — Implementar aplicação de teto por despesa (RN-001, RN-002, RN-004 — passo 9)
  - **O que faz:** aplica o passo 9 da ordem de aplicação. Para despesas
    elegíveis (não recusadas e não em revisão manual), aplica o teto da
    categoria. Se a data estiver no conjunto de dias de viagem, aumenta o teto
    em 50% — uma única vez, sem acúmulo. Reembolsa no máximo o valor informado.
    Registra todos os motivos aplicáveis na ordem de aplicação: `dentro_do_limite`
    quando o valor não atinge o teto; `limite_aplicado` quando o teto corta;
    `limite_viagem_aplicado` quando o teto ampliado é utilizado (combinado com
    `dentro_do_limite` ou `limite_aplicado` conforme o caso).
  - **Atende:** RN-001, RN-002, RN-004, AMB-001, AMB-002, FURO-003, FURO-005,
    FURO-006
  - **Aceite:**
    - `test_rn001_alimentacao_abaixo_teto` R$ 38,00 → R$ 38,00, motivo
      `dentro_do_limite`.
    - `test_rn001_alimentacao_acima_teto` R$ 72,50 → R$ 60,00, motivo
      `limite_aplicado`.
    - `test_rn001_transporte_abaixo_teto` R$ 75,00 → R$ 75,00, motivo
      `dentro_do_limite`.
    - `test_rn001_transporte_acima_teto` R$ 100,00 com nota → R$ 80,00, motivo
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
  - **O que faz:** aplica o passo 10. Arredonda cada valor monetário por
    despesa para duas casas (terceiro algarismo 0–4 para baixo; 5–9 para cima)
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

## Fase 3 — Validação estrutural, período e lote vazio

- [ ] **T-015** — Validação estrutural completa de entrada
  - **O que faz:** testa todas as situações de erro estrutural que interrompem
    o lote inteiro sem gerar resultado parcial. Complementa T-003 com cenários
    que exigem lote montado (não apenas parser unitário).
  - **Atende:** contrato de entrada seção 4, RN-010, FURO-015
  - **Aceite:**
    - `test_estrutural_json_malformado` JSON inválido → código != 0, sem
      arquivo de saída criado.
    - `test_estrutural_propriedade_extra_raiz` campo extra na raiz interrompe
      o lote.
    - `test_estrutural_propriedade_extra_periodo` campo extra em `periodo`
      interrompe o lote.
    - `test_estrutural_id_espacos_duplicado` IDs `"d-001"` e `" d-001 "`
      tratados como duplicados após remoção de espaços.
    - `test_estrutural_data_impossivel` `"2026-02-30"` rejeitada.
    - `test_estrutural_infinity_valor` `Infinity` em `valor` rejeitado.
    - `test_estrutural_sem_saida_parcial` em qualquer erro estrutural, arquivo
      de saída preexistente permanece intacto.
  - **Commit:**

- [ ] **T-016** — Validação de competência e período (RN-011)
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
  - **Commit:**

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

## Fase 4 — Integração ponta a ponta

- [ ] **T-018** — Integração do núcleo com o lote de exemplo completo
  - **O que faz:** executa o núcleo de cálculo (sem CLI) sobre
    `despesas-exemplo.json` com `data_calculo` fixada em `2026-07-31`. Verifica
    o status, `valor_reembolsavel` e a lista completa e ordenada de códigos de
    motivo de cada uma das 14 despesas. O lote contém hospedagens em
    `2026-07-14` e `2026-07-22` (dias de viagem: `2026-07-15` e `2026-07-23`).
  - **Atende:** todas as RNs (integração)
  - **Aceite:** `test_integracao_lote_completo` verifica para cada despesa:
    - d-001 → `revisao_manual`, valor `"0.00"`, motivos
      `[revisao_manual_viagem]`.
    - d-002 → `revisao_manual`, valor `"0.00"`, motivos
      `[revisao_manual_viagem]`.
    - d-003 → `recusada`, valor `"0.00"`, motivos `[nota_fiscal_ausente]`.
    - d-004 → `recusada`, valor `"0.00"`, motivos `[nota_fiscal_ausente]`.
    - d-005 → `recusada`, valor `"0.00"`, motivos `[categoria_fora_politica]`.
    - d-006 → `revisao_manual`, valor `"0.00"`, motivos
      `[revisao_manual_viagem]`.
    - d-007 → `recusada`, valor `"0.00"`, motivos `[duplicata]`.
    - d-008 → `recusada`, valor `"0.00"`, motivos `[prazo_excedido]`.
    - d-009 → `recusada`, valor `"0.00"`, motivos
      `[valor_negativo_fora_escopo]`.
    - d-010 → `revisao_manual`, valor `"0.00"`, motivos
      `[revisao_manual_viagem]`; descrição informa que as diárias são
      indetermináveis.
    - d-011 → `reembolsada`, valor `"33.33"`, motivos
      `[limite_viagem_aplicado, dentro_do_limite]`.
    - d-012 → `revisao_manual`, valor `"0.00"`, motivos
      `[revisao_manual_viagem]`; descrição informa que a data não foi
      identificada como dia de viagem.
    - d-013 → `recusada`, valor `"0.00"`, motivos `[nota_fiscal_ausente]`;
      ainda gera o dia de viagem `2026-07-23`.
    - d-014 → `revisao_manual`, valor `"0.00"`, motivos
      `[revisao_manual_viagem]`.
    - Totais exatos: `valor_reembolsavel: "33.33"` e
      `valor_em_revisao: "753.60"`.
  - **Commit:**

- [ ] **T-019** — Integração CLI via subprocesso
  - **O que faz:** invoca `reembolso calcular --input --output` via
    `subprocess` com arquivo temporário, verifica código de retorno, JSON
    válido na saída e campos obrigatórios do contrato.
  - **Atende:** RN-010, contrato de saída seção 4
  - **Aceite:**
    - `test_cli_integracao_subprocess` invoca a CLI com
      `despesas-exemplo.json`; verifica código 0; carrega a saída e confirma
      `versao_schema: "1.0"`, `moeda: "BRL"` e `data_calculo` no formato
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
  - **Commit:**

---

## Fase 5 — Envelope (criar no Dia 2)

> Novas tasks a partir da mudança de requisito recebida no Dia 2. Numeração
> continua em T-021 — não reiniciar e não renumerar as tasks anteriores.

---

## Cobertura

| Regra / Decisão | Task(s) | Teste(s) representativo(s) |
|---|---|---|
| RN-001 | T-013 | `test_rn001_alimentacao_acima_teto`, `test_rn001_transporte_acima_teto` |
| RN-002 | T-013 | `test_rn001_alimentacao_acima_teto` |
| RN-003 | T-010 | `test_rn003_exato_100_sem_nota`, `test_rn003_abaixo_100_sem_nota` |
| RN-004 | T-011, T-012, T-013 | `test_rn004_duas_hospedagens_geram_dois_dias`, `test_rn004_hospedagem_sem_nota_ainda_gera_dia` |
| RN-005 | T-009 | `test_rn005_prazo_exato_90_dias`, `test_rn005_prazo_91_dias` |
| RN-006 | T-008 | `test_rn006_duplicata_basica`, `test_rn006_valores_numericamente_iguais` |
| RN-007 | T-007 | `test_rn007_categoria_maiuscula`, `test_rn007_categoria_fora_politica` |
| RN-008 | T-006 | `test_rn008_valor_negativo`, `test_rn008_valor_subcentavo_0_004` |
| RN-009 | T-014 | `test_rn009_arredondamento_para_cima`, `test_rn009_total_soma_arredondados` |
| RN-010 | T-001, T-005, T-019 | `test_cli_integracao_subprocess` |
| RN-011 | T-003, T-016 | `test_rn011_inicio_fora_competencia`, `test_rn011_fim_mes_posterior_aceito` |
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
| FURO-015 | T-003, T-015 | `test_parser_propriedade_extra_raiz`, `test_estrutural_propriedade_extra_periodo` |
| FURO-016 | T-005 | `test_cli_rejeita_mesmo_arquivo` |
| FURO-017 | T-005 | `test_cli_data_calculo_na_saida` |
