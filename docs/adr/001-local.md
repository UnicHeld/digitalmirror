# ADR-001 — Execução local

Status: aceito no planejamento v0.1; atualizado pelo [ADR-007](007-docker-compose.md).
Contexto: o histórico contém dados privados e deve funcionar sem internet (RNF-08/09).
Decisão: persistência local e API somente `127.0.0.1:8765`, com proteção de sessão,
Host, Origin e CSRF. Sem cloud, broker ou envio de telemetria. A exclusão inicial
de containers foi substituída: execução local obrigatória em Docker/Compose.
Consequência: instalação e backup são responsabilidade local. Mesma conta do SO
não é fronteira de isolamento. Alternativa rejeitada: servidor externo.
