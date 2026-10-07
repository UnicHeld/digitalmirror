# ADR-002 — Monólito modular Python

Status: aceito no planejamento v0.1; base do pacote criada no EP-01/02.
Contexto: alvo Debian 12/Python 3.11+ e budgets de CPU/RSS.
Decisão: coletor, métricas, SQLite e API em um processo; fila limitada e um escritor.
Native Messaging pode usar bridge pequena. Adaptadores substituíveis, sem interfaces vazias.
Consequência: medições determinam conexão nativa; Uvicorn futuro terá um worker.
Conforme [ADR-007](007-docker-compose.md), o processo principal e a bridge Python
executam em contêiner; Docker/Compose substituem instalação Python direta no host.
Alternativas rejeitadas: Electron e serviços distribuídos pelo custo adicional.
