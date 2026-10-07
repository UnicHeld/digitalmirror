# EP-02 — Relatório inicial sanitizado

**Evidência histórica anterior ao ADR-007:** os comandos/medições desta seção
foram executados diretamente no primeiro spike e foram preservados. Não são
instruções vigentes: novas execuções e validações são obrigatoriamente via Docker.

Data: 06/10/2026. Execução de referência terminada às 23:31:23 UTC.
Status: **spike parcial; C0 pendente**. EP-01 validado localmente; EP-03 não iniciado.
Nenhuma telemetria pessoal ou conteúdo bruto das fontes foi versionado.

## Ambiente e fontes

Debian 12 (bookworm), Python 3.11.2, GNOME Shell instalado 43.9 e systemd 252.39.
A CLI desta execução não herdou DISPLAY, XDG_SESSION_TYPE, XDG_SESSION_ID,
DBUS_SESSION_BUS_ADDRESS, XDG_RUNTIME_DIR ou XAUTHORITY. Isso descreve o ambiente
do processo; não prova que o computador esteja sem sessão gráfica.

Ferramentas encontradas: xprop, xrandr, xdotool, xprintidle, gdbus, busctl e systemctl.
Pacotes consultados: x11-utils 7.7+5, x11-xserver-utils 7.7+9+b1,
xdotool 3.20160805.1-5, xprintidle 0.2.5-2, GLib 2.74.6 e coreutils 9.1.
O XML ScreenSaver foi lido do recurso instalado do GNOME Shell e confirma
GetActive (bool) e ActiveChanged (bool); isso não confirma acesso ao serviço da sessão.

| Fonte | Resultado real | Consequência/fallback |
| --- | --- | --- |
| X11 foco, classe, PID, workspace, geometria | Indisponíveis: missing-display | App/monitor desconhecidos; sem reutilizar último foco |
| XScreenSaver via xprintidle | Indisponível: missing-display | UNKNOWN quando não há lock confirmado |
| XRandR/monitores | Indisponível: missing-display | Monitor desconhecido; não presumir quantidade/principal |
| GNOME GetActive | Indisponível: missing-session-bus | Avaliar LockedHint da sessão gráfica validada |
| logind LockedHint | Indisponível: missing-graphical-session-id | Não consultar outra sessão; sem fonte crítica, UNKNOWN |
| logind Manager/PrepareForSleep | Introspecção disponível nas seis amostras | Eventos reais ainda não validados |
| graphical-session.target do usuário | Não testado: missing-user-session | Verificar no GNOME real antes de escolher autostart |
| Abas/perfis | Não testado; extensão não implementada | Preservar app browser e detalhamento desconhecido |

Consulta adicional de introspecção system D-Bus executada com saída descartada:
sucesso. Busca de XML em arquivos soltos não encontrou a interface; leitura via
`gresource extract` encontrou o contrato no pacote instalado. Acesso ao XML remoto
pelo navegador da ferramenta falhou; a evidência da interface veio do pacote local.
Manuais públicos de logind e Chrome foram consultados como referências técnicas,
sem substituir os ensaios reais.

## Custo básico medido

Comando executado:

```bash
.venv/bin/digitalmirror doctor --samples 6 --interval 5 --watch-seconds 2
```

Retorno **1**, diagnóstico degradado esperado pela falta de fontes gráficas.
As seis leituras de logind tiveram sucesso; demais fontes ficaram ausentes.
Nenhuma credencial ou variável de sessão foi recuperada de outros processos.

| Medida | Resultado |
| --- | --- |
| Amostras / intervalo nominal | 6 / 5s |
| Janela medida do polling | 25,020177s |
| Latência p95 por ciclo | 0,043727s |
| Atraso p95 de início do ciclo | 0,000214s |
| CPU própria na janela | 0,015453s |
| CPU dos subprocessos na janela | 0,063372s |
| CPU média de um núcleo na janela | 0,315% |
| RSS máximo próprio | 13.716 KiB |
| Maior RSS máximo de um filho | 13.716 KiB; não soma simultânea |

Startup e watcher não fazem parte da janela de custo acima. Filho pode herdar o
RSS inicial do processo pai; esse máximo não informa memória total simultânea.
Somente logind estava consultável: esses valores **não** validam custo de X11,
GNOME lock, browser, armazenamento, API, bridge, dashboard ou as RNF de 8h.
Precisão de foco/transições não foi medida; atraso de agendamento não é precisão de foco.

O watcher real de logind ficou conectado por 2,001892s, sem sinais: true=0,
false=0, status `no-events`. O watcher GNOME não iniciou pela fonte indisponível.
Não houve pedido de lock, suspensão, inputs, alteração de foco ou autostart.
Zero eventos não valida suspensão/retomada.

## Validação e pendências

Checks locais executados em Python 3.11: formatter Ruff, lint Ruff, mypy estrito
no pacote, 25 testes unittest e build sdist/wheel. Testes incluem parsers, privacidade,
timeout, limite de saída, erro de filho, cleanup do watcher, CLI e 16 fixtures.
Wheel instalado em venv isolado, sem dependências: entrypoint e doctor JSON
funcionaram (degradado/retorno 1 no mesmo ambiente). Verificado que o sdist inclui
fixtures, schema e rastreabilidade necessários aos testes.
O workflow de CI inclui Python 3.11/3.13; execução remota e Python 3.13 local não
foram realizados. Erros iniciais de lint/tipagem foram corrigidos e checks repetidos.

Ainda necessários conforme [protocolo](spike-ep02.md):

- X11/GNOME efetivamente herdados, fontes saudáveis e teste de dois monitores.
- Lock/unlock reais, comparação GetActive/ActiveChanged/LockedHint.
- Par PrepareForSleep true/false durante suspensão/retomada reais.
- Precisão de foco e custo de polling com todas as fontes saudáveis.
- Integração gráfica pós-login/logout/reboot e instância única.
- Prova de correlação de duas janelas/perfis com extensão de diagnóstico.
- Confirmação do almoço, navegador e quantidade de perfis/monitores antes da coleta contínua.

Decisão: manter GNOME/logind como candidatos; subprocessos limitados ao spike.
Sem evidência real, não fixar adaptador final, declarar C0 atingido ou avançar ao EP-03.
Metas de desempenho completas permanecem no EP-09. Na coleta dessa evidência
inicial, nenhuma issue/Project havia sido alterada e nenhum commit/push havia sido feito.

## Atualização — execução via Docker/Compose (ADR-007)

Docker client 29.8.1, Compose 5.5.1 e daemon **rootless 28.2.2** disponíveis.
Imagens `digitalmirror-dev:3.11` e `digitalmirror-runtime:3.11` construídas com
base bookworm; dependências Python/sistema instaladas somente durante o build.
Não houve instalação/reconfiguração do daemon ou criação de venv no host nessa migração.

Validações executadas via Compose:

- Configuração base e override desktop com variáveis sintéticas: válidas.
- Modelo resolvido confirma dev sem rede/sessão, desktop em rede host, capabilities
  removidas, filesystem read-only e nenhuma porta publicada.
- Fluxo `sh scripts/compose run --rm dev`: formatter check, lint, mypy, **32 testes**
  e build sdist/wheel passaram dentro do contêiner, sem rede.
- Launchers cobrem UID/GID rootful/rootless, ausência de sessão, Wayland, falta de
  Xauthority e arquivo indevidamente usado como socket, sem chamar Docker no preflight inválido.
- Artefatos/arquivos editados dentro do contêiner mantiveram UID/GID 1000:1000 no host.
- Doctor dev sem sockets: JSON válido, diagnóstico degradado/retorno 1 esperado.
- Runtime rootless com somente socket D-Bus de sistema montado read-only:
  introspecção PrepareForSleep disponível; fontes gráficas continuam ausentes.
- Launcher desktop real sem ambiente de sessão: recusou corretamente com código 2.

Falhas encontradas e corrigidas: Buildx tentou escrever estado em ~/.docker fora
do sandbox; build executado após autorização da ferramenta. UID 1000 interno no
daemon rootless não podia editar os bind mounts; launcher passou a usar UID/GID 0
internos, que mapeiam ao usuário não privilegiado do host. Stubs executáveis dos
novos testes não podiam executar no tmpfs /tmp (noexec); passaram a usar diretório
sintético temporário no workspace. Os checks foram repetidos após essas correções.

CI remota e imagem Python 3.13 não executadas nesta migração. Montagem/autenticação
da sessão GNOME/X11 completa, foco, dois monitores/perfis, lock/sleep e autostart
permanecem pendentes; leitura de logind não encerra C0.

A API ainda não existe. Rootless anterior a Engine 29.5 não compartilha a rede real
do host em network_mode host; o daemon atual atende checks/doctor por sockets, mas
precisa de versão compatível e validação no EP-07 antes da API em loopback.
Limitação registrada no ADR-007; Docker não foi atualizado automaticamente.
Não foram medidas novas metas de 8h ou overhead do Docker. Evidências anteriores
não foram reaproveitadas como benchmark da execução em contêiner.
