# Motor de Cálculo de Reembolso

CLI para avaliar despesas corporativas contra a política vigente, preservar
justificativas por item e emitir o resultado em JSON.

## Requisitos

- Python 3.11 ou superior
- Os arquivos de despesas, política e cotações em JSON

## Instalação

```powershell
python -m pip install -e ".[dev]"
```

## Execução

Os caminhos dos quatro arquivos são obrigatórios:

```powershell
reembolso calcular `
  --input exemplos\envelope\despesas-envelope.json `
  --output resultado.json `
  --policy exemplos\envelope\politica-v4.json `
  --exchange-rates exemplos\envelope\cambio.json
```

O campo `moeda` das despesas é opcional; quando omitido, o valor é considerado
BRL. A política, o câmbio e a data do cálculo são validados antes de gravar a
saída. A aplicação não consulta a rede. Se não houver cotação histórica
utilizável para uma moeda, somente a despesa correspondente será recusada.
Saídas preexistentes são preservadas quando há erro de entrada ou configuração.

Para executar o exemplo de centro de custo sem cadastro:

```powershell
reembolso calcular `
  --input exemplos\envelope\despesas-envelope-cc-desconhecido.json `
  --output resultado-desconhecido.json `
  --policy exemplos\envelope\politica-v4.json `
  --exchange-rates exemplos\envelope\cambio.json
```

## Testes e qualidade

```powershell
python -m pytest
ruff check .
ruff format --check .
```

## Contratos e decisões

- [Spec funcional](specs/001-motor-reembolso/spec.md)
- [Plano técnico](specs/001-motor-reembolso/plan.md)
- [Tasks e rastreabilidade](specs/001-motor-reembolso/tasks.md)
- [Log de decisões](specs/001-motor-reembolso/DECISIONS.md)
