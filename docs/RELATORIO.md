# Relatório — Desafio SDD

**Aluno:** DANILO CARDOSO ALVES · **Repositório:** https://github.com/daniloc9208/sdd-desafio · **Data deste rascunho:** 2026-10-16

> **Status:** relatório parcial. O motor está implementado e a suite de 177
> testes passa com `ruff check .` e `ruff format --check .` limpos.
> Os campos marcados para o responsável devem ser completados antes da entrega.

> Isto não é redação. São **evidências**. Toda afirmação deve vir acompanhada de
> arquivo, hash de commit ou trecho de sessão exportada. Um parágrafo bonito sem
> evidência vale menos que uma frase curta com um hash.
>
> Vale 20 dos 100 pontos, e é a seção que mais separa notas.

---

## Delegação

*O que você fez, o que o GitHub Copilot fez, e por que dividiu assim.*

**A divisão:**

| Atividade | Quem | Por quê |
|---|---|---|
| Identificar ambiguidades | GitHub Copilot + responsável | Copilot cruzou o enunciado e o JSON de exemplo; o responsável confirmou e ampliou as perguntas em `pendencias.MD`. |
| Decidir as ambiguidades | Responsável pelo produto | As decisões de negócio foram fornecidas pelo responsável; o agente não escolheu interpretações silenciosamente. |
| Escrever a spec | GitHub Copilot, com revisão do responsável | O agente organizou regras e contratos; o responsável corrigiu e aprovou as interpretações. |
| Desenhar a arquitetura | Responsável + GitHub Copilot | O responsável escolheu Python; o agente propôs arquitetura e ferramentas, aprovadas pelo responsável e registradas no plano. |
| Implementar | Codex (T-001 a T-012, sessão 05) + Axet Plugin (T-013 a T-027, sessão 04) | Motor implementado em `src/reembolso/`; 177 testes passam. Codex usou subagentes para frentes independentes (T-004, T-005, T-021, T-023, T-006 em paralelo). |
| Escrever testes | Codex + Axet Plugin, com critérios de aceite do `tasks.md` | Suite executável em `tests/`; todos os aceites de T-001 a T-026 cobertos e verificados. |
| Absorver o envelope | Spec + implementação | Requisitos do envelope implementados; T-025 valida os dois fixtures ponta a ponta. |

**Onde deleguei e me arrependi:**

Na primeira proposta de ordem das regras, o agente sugeriu tratar valores negativos
como créditos contra reembolsos e até informar desconto em folha. Essa proposta
excedia o escopo de uma plataforma de reembolsos. O responsável corrigiu a
interpretação antes de qualquer implementação; ver o caso em Discernimento.

**Onde não deleguei e deveria ter delegado:**

Até o momento não identificado.

**Usei subagentes / skills / MCP / hooks?** Na especificação e no plano não usei subagentes.
Na implementação, o Codex CLI (sessão 05) usou subagentes explicitamente para frentes
independentes do roadmap: T-004 (serializador), T-005 (I/O), T-021 (política), T-023
(câmbio) e T-006 (valor) rodaram em paralelo com a frente principal, evidenciado nos
logs da sessão 05. O Axet Plugin não usou subagentes na sessão 04.

---

## Descrição

*Como você transformou requisito ambíguo em requisito verificável.*

Pegue **um** requisito ambíguo da política do RH e mostre a evolução:

**Versão inicial registrada na spec (commit `c77c9cf`):**
> ```
> Despesas devem ser lançadas dentro do período de competência; a interpretação
> de “lançadas” e a relação com as datas presentes na entrada estão pendentes
> (AMB-005).
> ```

**Versão final:**
> ```
> Capturar a data local uma única vez no início da execução e registrá-la em
> `data_calculo`. Recusar despesas futuras ou com mais de 90 dias corridos;
> exatamente 90 dias ainda é elegível. O período informado não substitui essa
> verificação.
> ```

**O que estava ambíguo:** a política falava em lançamento dentro da competência,
mas a entrada não contém data de lançamento. Também não especificava a data de
referência nem se o limite de 90 dias era inclusivo.

**Como percebi:** ao revisar a regra contra o formato de entrada, identifiquei
que existe a data da despesa, mas não uma data de lançamento. Por isso defini a
data local do cálculo como referência; a spec também determina capturá-la uma
vez no início do lote para manter o resultado reproduzível. A decisão está
registrada em `docs/sessions/02-spec-plan-tasks.md` e em AMB-005.

**Evidência da primeira versão:** commit inicial `c77c9cf`.
**Commit da versão final:** a spec foi evoluindo ao longo dos commits da fase de
especificação; a versão final está em `specs/001-motor-reembolso/spec.md` e
a evolução está registrada em `DECISIONS.md` (D-001 a D-005).

---

## Discernimento

*Onde o GitHub Copilot errou e eu percebi.*

> **Sem um caso concreto e verificável, esta seção vale zero.** Não existe projeto
> de dois dias em que o modelo acertou tudo. A ausência do caso não prova que o
> modelo foi perfeito — prova que ninguém estava conferindo.

### Caso 1 — Interpretação de valores negativos

**O que ele propôs:** na primeira sugestão de ordem de aplicação, o agente
propôs aplicar despesas negativas como créditos contra despesas positivas e
sugerir desconto em folha se o saldo ficasse negativo.

**Por que estava errado:** o responsável esclareceu que a plataforma trata
reembolsos e que estornos pertencem a outro fluxo. Valores negativos não devem
alterar o total reembolsável.

**Como detectei:** ao revisar a proposta de ordem antes da implementação,
percebi que tratar estornos como créditos e sugerir desconto em folha ampliava
o escopo da plataforma de reembolsos.

**O que eu fiz:** decidi que valores negativos devem ser recusados por despesa
e que estornos pertencem a outro fluxo; pedi que a spec refletisse essa regra.
O Copilot atualizou AMB-009, RN-008 e a ordem de aplicação. A mudança está
registrada em D-001/D-003 no log de decisões. Isso foi corrigido antes de
existir código ou teste de produto, portanto não há rework de implementação
registrado.

**Onde está a evidência:** proposta do agente em
[sessão 02](sessions/02-spec-plan-tasks.md#L254) e correção do responsável
[na mesma sessão](sessions/02-spec-plan-tasks.md#L330); regra final em
[spec.md](../specs/001-motor-reembolso/spec.md#L220).

---

## Diligência

*O que você verificou antes de aceitar.*

**Verificações registradas nesta etapa:** o Copilot comparou os documentos com
a spec e o JSON de exemplo, consultou diagnósticos do VS Code, rodou
`git diff --check`, fez parse do JSON de referência, calculou as fronteiras de
90/91 dias e conferiu o total de revisão do lote integrado. O registro mostra
que eu pedi revisões e corrigi decisões de negócio; não permite confirmar que
li cada diff completo antes de aceitar todas as alterações.

**Li o diff inteiro em que porcentagem das entregas?** Não há percentual
registrado no histórico. Preencher com a estimativa honesta do responsável.

**O que aceitei sem verificar direito, e o que me custou:** a proposta de
tratar estornos como crédito foi corrigida antes da implementação. O histórico
não registra custo de código/testes; não atribuir custo não observado.

**Testes: quem escreveu, e como você sabe que eles testam a coisa certa?** Os
critérios de aceite foram elaborados pelo agente e revisados pelo responsável em
`tasks.md`. O agente implementou a suite em `tests/`; todos os 177 testes passam
(`python -m pytest`). Cada teste é identificado com o ID de tarefa e a RN
correspondente. Os valores esperados nas integrações (totais, status, motivos)
foram calculados manualmente a partir dos fixtures antes de escrever o código.

---

## O envelope

*A mudança de requisito do Dia 2.*

**Status:** requisitos do envelope implementados e validados. T-025 executa os
dois fixtures (`despesas-envelope.json` e `despesas-envelope-cc-desconhecido.json`)
ponta a ponta, verificando todos os status, valores e totais esperados.
**Quantos arquivos toquei na mão:** não medido para a absorção original; nesta
revisão foram criados `engine.py`, `rounding.py`, `__main__.py`, `cli.py`
(completo), `test_integration.py` e `test_rounding_totals.py`.
**Quanto tempo levou:** não medido.
**Diff de absorção:** ainda não calculado.

**Absorveu de graça:** na especificação, política e cotações externas, moedas
estrangeiras, conversão histórica offline e schema de saída 2.0 foram
acomodados sem consulta de rede durante o cálculo. A implementação foi
concluída em T-021, T-022, T-023, T-024 e validada em T-025 com os dois
fixtures do envelope.

**Resistiu:** aprovação manual acima de R$ 500 ficou fora do escopo, conforme
decisão registrada na spec.

**Ordem em que fiz:** envelope analisado, decisões registradas em
`pendencias.MD`/`DECISIONS.md`, contratos incorporados à spec e critérios
refletidos em `tasks.md` antes de retomar a implementação.

**Se eu tivesse escrito a spec original sabendo desta mudança:** Seria mais assertivo desde o início, visto que já teria todos os cenários e regras macro.

**O que a spec me poupou, em concreto:** Não tive quase nenhum trabalho manual, pois a regra em sí estava estabelecida. A IA apoiou nas diferenças e apenas defini as regras ambiguas.

---

## Fechamento

**Para qual tamanho de projeto isto valeu a pena?** Entendo que para qualquer tipo de projeto vale a pena, pois apoia demais num desenvolvimento mais assertivo.

**Para qual não valeria?** Não tenho ainda opinião formada sobre isso.

**O que eu faria diferente:** Se as entradas pudessem ser alteradas, muita coisa seria diferente, talvez até mais fácil. 

**A coisa mais desconfortável que aprendi sobre como eu trabalho com IA:**
Sentir tentado a aceitar tudo que é proposto por cansaço de conferir o que ocorre.
