# Plano — EP-02

1. Criar `src/digitalmirror/cli.py` e `doctor.py` sem dependências de runtime.
2. Encapsular subprocessos com argumentos fixos, sem shell, timeout e saída
   descartada após parse. Locale C para parsers; nenhum comando de mutação.
3. Diagnosticar X11 por xprop, xdotool somente `getwindowgeometry`, xrandr
   somente `--listactivemonitors`, idle por xprintidle; nunca solicitar título.
4. GNOME via GetActive, logind via propriedades da sessão explicitamente presente
   no ambiente e introspecção do Manager. Não assumir que LockedHint é confiável
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

ADRs existentes preservados. ADR-006 limita uso de subprocessos ao spike.
Testes substituem o runner para cenários sintéticos; subprocessos reais só no doctor.
Não adicionar resolução de abas sem extensão, armazenamento, serviço ou API.
ADR-007 torna Docker/Compose obrigatório: dependências de sistema na imagem,
mounts explícitos da sessão no desktop; testes/checks sem rede/sessão no dev.
