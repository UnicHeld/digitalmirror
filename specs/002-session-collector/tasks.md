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
- [x] US-02.2: suspensão/retomada voluntárias no GNOME com um par PrepareForSleep ordenado e saída final após retorno, informados pelo usuário.
- [ ] US-02.2: correlacionar ações/ciclos de bloqueio, comparar GetActive/LockedHint da sessão e revalidar fontes após retomada.
- [x] US-02.2/03: implementar resolução validada da sessão e UID real no Compose (ADR-010).
- [x] US-02.2: implementar contagens de lock durante watcher e revalidação após par de retomada/fim.
- [x] US-02.2 / RNF-09: testar validação de identidade, falhas, divergências e recuperação sanitizadas via Compose.
- [ ] US-02.2: investigar session-identity-mismatch do primeiro doctor real ADR-010, com motivos/proveniência sanitizados antes de corrigir associação.
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
pendente, sem comparação LockedHint/GetActive bloqueado. Ensaio posterior de
180s com suspensão/retomada manual recebeu um ciclo completo logind e um GNOME,
sem duplicatas/bordas pendentes; fontes X11/GetActive após retorno não revalidadas.
RNF-03 não atendida na janela curta de
polling (1,137% > 1%); estabilidade de 8h, foco, perfis, autostart e C0 pendentes.

Etapa 1 implementada conforme ADR-010: User.Display ou ID explícito validados,
host UID preservado no mapeamento rootless, contagens de lock e revalidações após
pares de retomada/fim. 53 testes, formatter, lint, mypy e build via Compose passaram.
Imagens dev/runtime reconstruídas; runtime com D-Bus de sistema e sem sessão
gráfica produz resumo/post_watch_checks degradados honestos. Candidato real com
DISPLAY sintético incorreto rejeitado. Formato JSON busctl validado no barramento
real, sem emitir identidade. Primeiro doctor real da etapa 1 recebido: dez fontes
read-ok, GNOME=false e logind-lock=session-identity-mismatch; atributo divergente
ainda desconhecido. Comparação de lock/retomada da versão nova ainda não testada.
Retomar da investigação descrita no handoff, sem iniciar EP-03.
