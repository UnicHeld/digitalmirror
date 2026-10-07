# Tarefas — EP-01 / #1

- [x] US-01.1: spec/plan/tasks e ADRs 001–006 publicados na main.
- [x] US-01.2: estados, unidades, qualidade, privacidade e rastreabilidade RF/RNF.
- [x] US-01.3: schema e 16 fixtures da seção 4.6 + casos negativos/fronteiras.
- [x] US-01.3 / RNF-10: testes de schema e coerência dos oráculos passam.
- [x] US-01.3: workflow CI descobre testes presentes/futuros; lint/tipos/build passam localmente e na CI Python 3.11/3.13 via Compose.
- [x] Documentação distingue contratos verificados de motor ainda não implementado.

Commit de implementação: `0a552a5`, publicado na main. Checklist da issue #1
concluído, issue encerrada e Project atualizado para Done.
[CI remota](https://github.com/UnicHeld/digitalmirror/actions/runs/37550585612)
passou em Python 3.11 e 3.13. EP-02/C0 permanecem pendentes.
Fluxo vigente após ADR-007: checks/build locais e CI executados via Docker/Compose;
a evidência da implementação inicial fora do contêiner é histórica.
