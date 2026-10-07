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
- [x] US-02.2: correlacionar bloqueio manual ao ciclo GNOME e revalidar fontes após retomada, pelo fallback documentado no ADR-010.
- [ ] US-02.2 / C0: registrar na decisão final de adaptadores que a comparação GetActive/LockedHint continua indisponível por Session.Display vazio.
- [x] US-02.2/03: implementar resolução validada da sessão e UID real no Compose (ADR-010).
- [x] US-02.2: implementar contagens de lock durante watcher e revalidação após par de retomada/fim.
- [x] US-02.2 / RNF-09: testar validação de identidade, falhas, divergências e recuperação sanitizadas via Compose.
- [x] US-02.2: identificar a comparação que causou session-identity-mismatch no doctor real; somente Session.Display vazio divergiu, sem corrigir/afrouxar associação.
- [x] US-02.2 / RF-04/16 / RNF-09: instrumentar proveniência persistente em falhas, seis comparações de identidade, categoria de DISPLAY e relação entre UIDs; preservar validação ADR-010 e privacidade.
- [x] US-02.2 / RNF-09: regressões de rejeições individuais/múltiplas, categorias de DISPLAY, erros antes das comparações e UID rootless; 57 testes/checks/build via Compose/Python 3.11 e imagens dev/desktop reconstruídas.
- [x] US-02.2: receber doctor simples reconstruído no terminal GNOME/X11 e identificar os atributos divergentes antes dos watchers novos.
- [x] US-02.2: registrar decisão de continuar ensaios pelo fallback GNOME existente, mantendo associação logind indisponível (ADR-010, evidência de 07/10).
- [x] US-02.2: registrar watcher real de 120s da versão instrumentada: um ciclo GNOME completo, 24 consultas read-ok (7 true/17 false) e dez fontes disponíveis ao fim; correlação com ações manuais ainda pendente.
- [x] US-02.2: suspensão manual/retomada informadas no watcher de 180s com um ciclo PrepareForSleep, revalidação acionada e propriedades da janela recuperadas ao fim após no-focused-window imediato.
- [x] US-02.2: esclarecer atalho informado; usuário corrigiu para Windows+L e confirmou bloqueio manual correlacionado ao único ciclo GNOME.
- [x] US-02.2: validar fallback GNOME com um bloqueio manual correlacionado a um ciclo e consultas true/false; suspensão/retomada com revalidações e recuperação final, sem alegar comparação LockedHint.
- [x] US-02.2: registrar evidência complementar do host: LockedHint acessível por candidato indicado por User.Display e self sem associação; não substituir o critério DISPLAY nem fixar ID.
- [ ] US-02.2: investigar associação passiva alternativa ao X11 antes de usar LockedHint com Session.Display vazio; documentar ADR/spec e validar transições se uma alternativa for comprovada.
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

Retomada de 07/10/2026: instrumentação sanitizada pronta e validada em Compose,
com 57 testes, formatter, lint, mypy e build aprovados. Doctor dev e imagem runtime
reconstruída, sem sockets gráficos, reportam degraded/código 1 esperado e
candidate_source=not-attempted. Ainda falta o objeto logind-lock do doctor no
terminal GNOME/X11 para identificar a divergência real; não foi corrigido nenhum
critério de associação nem executado watcher gráfico nesta retomada.

Doctor real das 22:32:01 UTC de 07/10 recebido: candidato user-display,
Id/UID/Type/Class/Remote confirmados; somente Session.Display vazio falhou.
GNOME=false, dez fontes read-ok, um monitor principal com janela atribuída.
Decisão documentada de ensaiar fallback GNOME, conservando logind-lock
indisponível. Watchers dessa versão ainda pendentes; C0 não atingido.

Watcher real de lock recebido (amostra inicial 23:01:16 UTC de 07/10): um ciclo
GNOME ordenado, sem duplicatas ou bordas pendentes; 24 consultas read-ok, true=7
e false=17. Dez fontes disponíveis ao fim, GNOME=false. logind-lock indisponível
24/24 e ao fim por Session.Display vazio, comparação unavailable=24. Falta relato
manual para correlacionar ações e aceitar fallback. Sem eventos de suspensão;
próximo ensaio separado de 180s deve validar revalidações após par de retomada.
C0 permanece pendente; não avançar ao EP-03.

Watcher real de suspensão recebido (amostra inicial 23:05:42 UTC de 07/10):
usuário relata suspensão manual por cerca de 15s e retomada. Um ciclo logind e um
GNOME completos, zero duplicatas/bordas pendentes; GetActive read-ok 35/35
(true=2/false=33). Um par de retomada acionou revalidação: X11 respondeu sem foco,
quatro propriedades da janela indisponíveis por no-focused-window; recuperaram
ao fim, com dez fontes read-ok. logind-lock continua indisponível por Display
vazio. Não interpretar foco vazio como falha de conexão ou fabricar último app.
Relato do primeiro lock recebido, mas atalho informado ficou ambíguo; esclarecer
bloqueio efetivo antes do aceite do fallback e avanço às próximas etapas.

Esclarecimento recebido: o atalho foi Windows+L para bloquear. Relato manual
corresponde ao único ciclo GNOME do ensaio isolado; fallback aceito no host.
Etapa 1 encerrada com bloqueio/desbloqueio e suspensão/retomada revalidados,
preservando leitura sem foco imediata/recuperação final e limitação LockedHint.
Seguir precisão de foco/monitores, dois perfis e login/logout/instância única.
C0 e decisão final de adaptadores pendentes; EP-03 permanece não iniciado.
