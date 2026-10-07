# ADR-004 — Métricas puras

Status: aceito no planejamento v0.1; implementação no EP-05.
Contexto: API, dashboard e exportação devem reconciliar os mesmos totais.
Decisão: funções puras recebem calendário, intervalos e política versionada;
recortam jornada/almoço e retornam E/D/P/O com denominadores explícitos.
Consequência: fixtures EP-01 serão oráculos do motor; null representa N/A.
Alternativa rejeitada: fórmulas duplicadas na interface e na API.
