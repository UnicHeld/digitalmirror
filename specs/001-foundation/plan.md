# Plano — EP-01

1. Publicar spec e tasks antes do código; materializar ADRs 001–005 existentes e
   registrar no ADR-006 a ferramenta diagnóstica de M0, sem substituir arquitetura final.
2. Mapear todos os RF-01–16 e RNF-01–10 em `docs/requirements.md`.
3. Definir JSON Schema Draft 2020-12 de fixtures com versões, calendário,
   intervalos UTC, qualidade, anotações e resultados esperados em segundos.
4. Criar fixtures sintéticas da seção 4.6, pausas, divisor zero e limites/falhas.
5. Usar `unittest` e `jsonschema` apenas em desenvolvimento para schema e
   coerência dos exemplos. Não implementar fórmulas de produção antecipadamente.
6. Criar pacote Python 3.11+ mínimo com layout `src`, CLI no EP-02 e CI com
   descoberta de testes, Ruff, mypy e build. Runtime M0 usa somente biblioteca padrão.
   Conforme ADR-007, ferramentas e Python ficam nas imagens Docker; CI e checks
   locais utilizam Compose e `scripts/check`, sem venv no host.

Validação: exemplos positivos/negativos do schema; conservação dos resultados
esperados; calendário, UTC e ordem dos intervalos. Motor futuro deve consumir
os mesmos inputs e comparar com `expected` (EP-05), sem reescrever o oráculo.
Semântica permanece a do produto v0.1; schemas e CLI de M0 têm versão 1.
