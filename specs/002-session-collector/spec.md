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

CLI retorna JSON versionado com fontes, motivos, fallback e medições agregadas.
`--watch-seconds` (0–900; padrão 0) observa ActiveChanged e PrepareForSleep em
streams limitados, mostrando somente contagens de true/false e status de conexão.
GetActive/ActiveChanged não é considerado prova de bloqueio sem ensaio comparativo.
Ausência de eventos não prova fonte funcional. Nenhum comando inicia lock/sleep.
Cada amostra revalida fontes; falhas posteriores ficam visíveis no histórico agregado.
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
