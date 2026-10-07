# Tarefas — EP-02 / #2

- [x] US-02.1: spec/plan/tasks e `doctor` passivo com falhas normalizadas.
- [x] US-02.1 / RF-16: testes de parsers, timeout, fonte ausente e saída sanitizada.
- [x] US-02.3: medidor de custo básico com CPU de filhos, RSS e atraso.
- [x] US-02.1: diagnóstico no ambiente disponível e relatório sanitizado local.
- [x] US-02.2: resumo de ciclos ordenados e sinais sem par conforme ADR-008.
- [x] US-02.2 / RNF-09/10: testes de ordem, duplicatas, isolamento entre fontes e falha do watcher via Compose.
- [x] US-02.1/03: launcher aceita XDG_SESSION_ID ausente; Compose e doctor preservam fallback seguro (ADR-009).
- [x] US-02.1: registrar evidência fornecida pelo usuário de leitura real via Compose de X11/GNOME e dois monitores, sem logs pessoais.
- [x] US-02.3: registrar polling real informado pelo usuário (12 amostras/5s), com disponibilidade estável e CPU de 1,137% acima da referência RNF-03.
- [x] US-02.2: registrar entrega real de dois ciclos GNOME no watcher de 120s durante ensaio manual Windows+L, sem inferir quantidade de bloqueios efetivos.
- [ ] US-02.2: bloquear/desbloquear e suspender/retomar manualmente no GNOME real.
- [ ] US-02.3: polling com fontes gráficas saudáveis e precisão de transição medida.
- [ ] US-02.3: confirmar ambiente gráfico e início único após login/logout reais.
- [ ] US-02.4: prova real com duas janelas/perfis e metadados da extensão.
- [ ] C0: decidir adaptadores finais a partir das evidências; liberar EP-03.

Após ADR-007, doctor e ferramentas executam via Compose. Leitura de logind em
runtime Docker rootless com socket de sistema foi verificada; leitura GNOME/X11
e dois monitores confirmada por resultado do terminal do usuário. Transições,
precisão e integração da sessão completa continuam pendentes.
Evidências iniciais diretas são históricas.
Resumo ordenado do watcher validado com streams sintéticos e CLI JSON/retorno
degradado após falha. Runtime Docker com logind observado por 2s: zero eventos,
zero ciclos e cycle_status=no-events; não confirma suspensão real.
Regressões do ID opcional passaram: preflight ainda exige Xauthority/sockets,
modelo Compose aceita ID vazio e doctor preserva fontes independentes sem consultar
outra sessão. 40 testes/checks/build passaram via Compose/Python 3.11.
Incremento publicado no commit `dfe2a24`; [CI via Compose](https://github.com/UnicHeld/digitalmirror/actions/runs/37553831948)
passou em Python 3.11/3.13, com 40 testes e imagens dev/runtime. Issue #2/Project
sincronizados: US-02.1 concluída, EP-02 In Progress e ensaios reais ainda pendentes.
Resultados posteriores do terminal: dez fontes disponíveis 12/12; GNOME recebeu
dois ciclos completos durante ensaio manual. Correlação com quantidade de ações
pendente, sem comparação LockedHint/GetActive bloqueado. PrepareForSleep sem
eventos; suspensão ainda não testada. RNF-03 não atendida na janela curta de
polling (1,137% > 1%); estabilidade de 8h, foco, perfis, autostart e C0 pendentes.
