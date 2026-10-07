# Tarefas — EP-02 / #2

- [x] US-02.1: spec/plan/tasks e `doctor` passivo com falhas normalizadas.
- [x] US-02.1 / RF-16: testes de parsers, timeout, fonte ausente e saída sanitizada.
- [x] US-02.3: medidor de custo básico com CPU de filhos, RSS e atraso.
- [x] US-02.1: diagnóstico no ambiente disponível e relatório sanitizado local.
- [x] US-02.2: resumo de ciclos ordenados e sinais sem par conforme ADR-008.
- [x] US-02.2 / RNF-09/10: testes de ordem, duplicatas, isolamento entre fontes e falha do watcher via Compose.
- [x] US-02.1/03: launcher aceita XDG_SESSION_ID ausente; Compose e doctor preservam fallback seguro (ADR-009).
- [ ] US-02.2: bloquear/desbloquear e suspender/retomar manualmente no GNOME real.
- [ ] US-02.3: polling com fontes gráficas saudáveis e precisão de transição medida.
- [ ] US-02.3: confirmar ambiente gráfico e início único após login/logout reais.
- [ ] US-02.4: prova real com duas janelas/perfis e metadados da extensão.
- [ ] C0: decidir adaptadores finais a partir das evidências; liberar EP-03.

Após ADR-007, doctor e ferramentas executam via Compose. Leitura de logind em
runtime Docker rootless com socket de sistema foi verificada; sessão GNOME/X11
completa continua pendente. Evidências iniciais diretas são históricas.
Resumo ordenado do watcher validado com streams sintéticos e CLI JSON/retorno
degradado após falha. Runtime Docker com logind observado por 2s: zero eventos,
zero ciclos e cycle_status=no-events; não confirma suspensão real.
Regressões do ID opcional passaram: preflight ainda exige Xauthority/sockets,
modelo Compose aceita ID vazio e doctor preserva fontes independentes sem consultar
outra sessão. 40 testes/checks/build passaram via Compose/Python 3.11.
