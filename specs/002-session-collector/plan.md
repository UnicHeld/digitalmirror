# Plano — EP-02

1. Criar `src/digitalmirror/cli.py` e `doctor.py` sem dependências de runtime.
2. Encapsular subprocessos com argumentos fixos, sem shell, timeout e saída
   descartada após parse. Locale C para parsers; nenhum comando de mutação.
3. Diagnosticar X11 por xprop, xdotool somente `getwindowgeometry`, xrandr
   somente `--listactivemonitors`, idle por xprintidle; nunca solicitar título.
4. GNOME via GetActive, logind via sessão explícita ou User.Display do UID real
   do host, com identidade e DISPLAY validados (ADR-010), e introspecção do Manager.
   Não assumir que LockedHint é confiável
   antes de ensaio real nem confundir introspecção com suspensão observada.
5. Verificar `graphical-session.target` via GetUnit e ActiveState no systemd user
   do host pelo socket D-Bus montado; não exigir systemd dentro do contêiner.
   Sem instalação/enable/linger nem hardcode de DISPLAY.
6. Polling finito com relógio monotônico, métricas CPU/RSS próprias e de filhos,
   latência p95 e atraso. Registrar sucesso/falha por fonte, sem guardar telemetria.
7. Publicar protocolo manual para sinais reais e correlação, executar o que o
   ambiente disponibilizar e registrar pendências sanitizadas.
8. Observação finita de eventos via `stdbuf -oL gdbus monitor`, com leitura
   incremental limitada, regex de dois sinais e contagens; sem stdout bruto.
   Encerrar/recolher filhos ao fim ou interrupção. Distinguir zero eventos de validação.
9. Conforme ADR-008, resumir a ordem true/false por fonte em memória constante:
   ciclos completos, início pendente, fim sem início e duplicatas. Preservar status
   de conexão; falhas invalidam confirmação mesmo após pares recebidos. Testar
   sequências invertidas, múltiplos ciclos, streams independentes e encerramento.
10. Conforme ADR-009, permitir XDG_SESSION_ID ausente no launcher/Compose.
    Preservar preflight dos sockets/cookie e fallback explícito de LockedHint;
    testar que nenhuma outra sessão logind é consultada.
11. ADR-010: resolução validada com JSON busctl; UID do host separado de UID
    rootless. Testar sessão incorreta, respostas inválidas e falha sem fallback.
12. Consultas de lock a cada 5s durante watcher; revalidações por par de retomada
    e fim. Contagens sanitizadas e falhas persistentes no status; testes sintéticos
    e integração de streams reais, seguidos por ensaio manual no terminal gráfico.
13. Instrumentar SessionResolution e logind-lock.details com proveniência,
    comparações booleanas, categoria de DISPLAY e relação entre UIDs sanitizadas.
    Preservar motivo agregado e validação; testar rejeições individuais/múltiplas,
    erros de consulta/parse, saída privada e UID interno rootless. Reconstruir
    imagens, executar checks via Compose e repetir doctor no terminal real antes
    de qualquer correção de associação ou ensaio lock/retomada.
14. Resultado real de 07/10: somente Session.Display vazio impede associação.
    Manter validação; executar ensaios existentes pelo fallback GNOME, sem novos
    comandos/fontes ou alterações de login. Documentar comparação logind ausente
    e status degraded esperado; correlacionar um ciclo de bloqueio com uma ação
    manual antes do ensaio separado de suspensão/retomada (ADR-010).

ADRs existentes preservados. ADR-006 limita uso de subprocessos ao spike.
ADR-011 complementa exclusivamente Display vazio: verificar VT/seat/atividade
do mesmo candidato e raiz X11, Seat.ActiveSession e releituras consistentes.
Manter recusa de demais divergências; testar falhas/corridas/privacidade, executar
checks/imagens via Compose e ensaios reais antes de aceitar LockedHint/transições.
Extensão de diagnóstico do ADR-005: emitir booleano de atribuição ao principal
com dados já lidos e principal único. Testar principal/secundário, maior interseção,
geometria ausente, janela fora das telas e principal ausente/ambíguo. Depois dos
checks/imagens, ensaios estáveis nas duas telas antes de instrumentar transições.
Testes substituem o runner para cenários sintéticos; subprocessos reais só no doctor.
Não adicionar resolução de abas sem extensão, armazenamento, serviço ou API.
ADR-007 torna Docker/Compose obrigatório: dependências de sistema na imagem,
mounts explícitos da sessão no desktop; testes/checks sem rede/sessão no dev.
