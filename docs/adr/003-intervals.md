# ADR-003 — Intervalos como base de verdade

Status: aceito no planejamento v0.1; implementação no EP-04.
Contexto: screenshots/inputs são invasivos e polling bruto aumenta volume.
Decisão: intervalos semiabertos UTC com durações monotônicas, origem, qualidade,
política e checkpoints ≤30s; gaps explícitos. Rollups são derivados/revisionados.
Consequência: crash não prolonga app; detalhes expirados limitam reconstrução.
Alternativa rejeitada: estado final de um bloco representando toda sua duração.
