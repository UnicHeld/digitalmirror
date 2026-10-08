# EP-02 — Spike passivo Debian/GNOME/X11

Issue: [#2](https://github.com/UnicHeld/digitalmirror/issues/2). Depende do EP-01.
Status: em implementação. Esta fatia cobre M0, sem implementar EP-03.
Execução vigente via serviço desktop Compose conforme ADR-007; fontes são da
sessão real do host. Serviço dev isolado diagnostica ausência de fontes.

## Histórias e requisitos

- US-02.1 / RF-02/03/04/09/16: `digitalmirror doctor` diagnostica sessão X11,
  `_NET_ACTIVE_WINDOW`, WM_CLASS/PID/workspace/geometria, idle, GNOME D-Bus,
  LockedHint/logind, PrepareForSleep, monitores e alvo gráfico systemd.
- US-02.2 / RF-04/05: ensaio manual de bloqueio/desbloqueio e suspensão/retomada,
  com observação somente leitura. Introspecção não prova entrega de eventos.
- US-02.3 / RF-15 / RNF-01/03/04: polling finito de 5s mede latência,
  atraso, RSS e CPU própria + filhos; alvo gráfico observado sem instalar/iniciar serviço.
  Custo básico de spike não equivale a soak de 8h.
- US-02.4 / RF-08 / RNF-10: protocolo de duas janelas/perfis testa correlação.
  Sem extensão, não inferir aba/hostname de título/PID; resultado permanece pendente.
- RNF-08/09: funciona sem internet e sem servidor/socket próprio.

## Comportamento observável

Given falta de DISPLAY, When executar doctor, Then foco/idle/monitores indisponíveis,
sem adivinhar `:0`, recuperar credenciais de outros processos ou atribuir presença.
Given Wayland ou sessão não confirmada como X11, Then diagnóstico de X11 indisponível.
Given erro, timeout ou resposta inválida, Then motivo normalizado, sem stderr pessoal.
Given fonte presente, Then testar leitura efetiva, sem confundir binário com fonte saudável.
Given logind acessível sem sessão gráfica identificada, Then não usar LockedHint de outra sessão.
Given terminal GNOME/X11 sem XDG_SESSION_ID, Then o launcher continua após validar
cookie/sockets e Docker local; GNOME/X11 são consultados e logind-lock usa
somente candidato validado. Falha de resolução mantém diagnóstico degradado.
Conforme ADR-010, resolver somente User.Display do UID real fornecido pelo launcher,
validando Id/UID/Type/Class/Remote/Display antes de LockedHint. Sem associação válida,
manter indisponível; ID explícito incorreto não gera busca de outro candidato.
Não enumerar sessões nem recuperar ambiente de outro processo.

Given rejeição do candidato, Then preservar `session-identity-mismatch` e emitir
em `logind-lock.details` a proveniência da tentativa (`candidate_source`) mesmo
na falha. Após parse tipado completo, emitir seis comparações `identity_*` como
booleans e `session_display_status` como enum local/empty/nonlocal-or-invalid.
Falha anterior ao parse completo não emite resultados parciais de identidade.
`process_uid_is_root` e `host_uid_matches_process_uid` distinguem as identidades
interna/host sem imprimir seus valores nem alterar a escolha do candidato.
`resolved_from_user_display` mantém a semântica anterior de sucesso. Sem ID/UID,
DISPLAY, paths ou propriedades brutas na saída; divergências múltiplas são
reportadas juntas. Requisitos RF-04/16 e RNF-09, extensão do ADR-010.

Given candidato User.Display com Id/UID/Type/Class/Remote confirmados e
Session.Display vazio, Then aplicar associação adicional do ADR-011; falha mantém
logind-lock indisponível. Prosseguir então
com ensaios independentes GNOME e PrepareForSleep conforme decisão ADR-010 de
07/10/2026; não inferir associação nem alterar a sessão. O aceite do fallback
GNOME exige ação manual correlacionada a ciclo ordenado e consultas true/false,
mais revalidação na retomada/fim. Comparação unavailable e diagnóstico degraded
são esperados nessa condição; LockedHint e concordância permanecem não validados.

Given Display exatamente vazio com os cinco outros critérios válidos, Then aceitar
o mesmo candidato somente com VT positivo igual ao XFree86_VT da raiz, seat0
canônico, Active=true e Seat.ActiveSession igual ao ID/path originais. Revalidar
as nove propriedades, VT X11 e ActiveSession antes de LockedHint. Display não
vazio divergente/inválido nunca usa essa alternativa. Erro/tipo inválido/mudança
rejeita, sem reutilizar sucesso anterior ou escolher outro candidato.
Emitir somente booleans/enum de associação, preservando identity_display_matches=
false/empty no caminho VT; não fabricar metadado. Leituras sequenciais não são
prova atômica; ensaios reais de lock/retomada e custo continuam necessários.

CLI retorna JSON versionado com fontes, motivos, fallback e medições agregadas.
Conforme ADR-005, detalhes XRandR incluem `focused_window_on_primary` somente
com janela atribuída e exatamente um monitor principal. true/false distinguem
principal/outro monitor; campo ausente mantém classificação desconhecida.
Sem nomes/coordenadas/IDs na saída, novas consultas ou mudança de crédito de foco.
Relato manual de foco estável verifica atribuição; não valida precisão de transições.
`--watch-seconds` (0–900; padrão 0) observa ActiveChanged e PrepareForSleep em
streams limitados, mostrando somente contagens de true/false e status de conexão.
Conforme ADR-008, cada fonte inclui `cycles` com `complete_count`, `pending_start`,
`unpaired_end_count` e `duplicate_signal_count`, mais `cycle_status`.
Given false seguido de true, Then não registrar ciclo completo: fim sem início e
início pendente ficam explícitos. Given true/true/false, Then contar um ciclo e uma
duplicata. Given conexão encerrada, Then cycle_status=failed, mesmo com pares já lidos.
Complete exige ao menos um true seguido de false, nenhum início pendente e nenhum
fim sem início na janela. Não há armazenamento do stream nem inferência de duração.
Campos existentes e schema_version=1 são preservados; o resumo é uma extensão aditiva.
GetActive/ActiveChanged não é considerado prova de bloqueio sem ensaio comparativo.
Ausência de eventos não prova fonte funcional. Nenhum comando inicia lock/sleep.
Cada amostra revalida fontes; falhas posteriores ficam visíveis no histórico agregado.
O watcher consulta GetActive/LockedHint a cada 5s e resume booleans/indisponíveis,
motivos e coincidências/divergências sem história pessoal. Cada par de suspensão
recebido provoca revalidação de todas as fontes; saída inclui resumo por fonte e
post_watch_checks no fim. Falha recuperada preserva status degraded. As consultas
são sequenciais e a comparação não é prova atômica de bloqueio.
`--samples` aceita 1–720; `--interval` aceita 5–60s finitos. Timeout de comando ≤2s;
execução sequencial pode ultrapassar o intervalo e deve reportar atraso sem simular amostras.
Código 0: fontes essenciais e auxiliares disponíveis; 1: diagnóstico degradado;
2: argumento inválido. Correlação/ensaios reais continuam explicitamente pendentes.

## Aceite e limites de encerramento

Relatório sanitizado com disponíveis/ausentes, fallbacks e custo básico; testes de
parsers, falhas, privacidade e CLI. Testar leitura real no alvo quando acessível.
Não encerrar US-02.2/03/04 nem C0 sem lock/unlock/sleep/resume, precisão de foco,
integração pós-login e correlação de dois perfis reais. Procedimento em
`docs/spike-ep02.md`. Não avançar ao EP-03 enquanto os pressupostos críticos estiverem pendentes.
