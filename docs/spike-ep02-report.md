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

## Publicação e CI — 06/10/2026

Implementação publicada na main no commit `0a552a5`, com handoff inicial em
`6cdf7f3`. [CI remota via Compose](https://github.com/UnicHeld/digitalmirror/actions/runs/37550585612)
passou em Python 3.11 e 3.13: configuração Compose, build das imagens dev/runtime,
formatter, lint, mypy, 32 testes e build sdist/wheel com artefatos publicados.
A CI não monta uma sessão gráfica real e não valida as pendências do spike.

Issues #1/#2/#8/#9 sincronizadas com as entregas e Docker/Compose. Issue #1
encerrada; Project privado atualizado: EP-01 Done, EP-02 In Progress e demais
épicos no Backlog. README do Project explicita Docker obrigatório.
EP-02/C0, RNF de 8h e validação de loopback rootless no EP-07 continuam pendentes.

## Continuação local — ciclos ordenados (ADR-008)

O watcher passa a distinguir true → false de false → true, contar duplicatas e
informar sinais sem par, mantendo os campos anteriores do JSON v1. O estado por
fonte não guarda histórico de eventos nem calcula duração. Conexão encerrada
continua failed mesmo após um ciclo recebido; CLI retorna 1 nesse cenário.

Validação local via Compose/Python 3.11: formatter, lint, mypy, **38 testes** e
build sdist/wheel passaram. Imagens dev/runtime reconstruídas. Seis novos testes
cobrem ordem invertida, duplicatas, bordas parciais, falha após par, streams
independentes/fragmentados, saída sanitizada e integração com CLI. A primeira
rodada de lint encontrou duas linhas longas; corrigidas e checks repetidos.

Runtime rootless com apenas D-Bus de sistema montado read-only: PrepareForSleep
consultável e watcher conectado por aproximadamente 2s. Resultado: zero sinais,
zero ciclos, nenhum início pendente e cycle_status=no-events. GNOME permanece
not-tested. Diagnóstico degradado/retorno 1 esperado pela ausência da sessão gráfica.
Nenhum comando provocou lock, suspensão ou mudança de foco.

O launcher de sessão real voltou a recusar execução sem GNOME/X11 com código 2.
Ensaios reais e C0 continuam pendentes. Na validação local dessa fatia, publicação
e CI Python 3.13 ainda não haviam ocorrido. A evidência anterior de CI cobre a
entrega de 32 testes; publicação e CI do incremento estão na seção seguinte.

## Correção do launcher — XDG_SESSION_ID ausente (ADR-009)

O usuário informou que o launcher recusou execução no terminal com
`XDG_SESSION_ID da sessão não foi recebido.`. Isso confirma somente ausência da
variável no ambiente daquele comando; não confirma falta da sessão gráfica.

O ID passa a ser opcional no preflight e no override Compose. Sem ele, X11/GNOME
e PrepareForSleep continuam consultáveis quando seus sockets estão disponíveis;
LockedHint fica indisponível com missing-graphical-session-id, mantendo o doctor
degradado/retorno 1. Nenhum ID ou ambiente de outro processo é recuperado.

Validações locais via Compose/Python 3.11: formatter, lint, mypy, **40 testes** e
build sdist/wheel passaram. Regressões verificam Xauthority/sockets obrigatórios
mesmo sem ID e fontes independentes sem GetSession/LockedHint de outra sessão.
Override Compose resolvido com variáveis sintéticas e XDG_SESSION_ID ausente:
ID vazio aceito; mounts read-only/create_host_path=false e ausência de portas
preservados. Sintaxe dos três scripts shell e git diff --check passaram.
Imagens dev/runtime reconstruídas com sucesso para este incremento.

Aguardando resultado do novo diagnóstico no terminal do usuário. O erro anterior
não valida foco, bloqueio, suspensão, monitores, perfis ou autostart. C0 continua
pendente.

Publicação concluída no commit `dfe2a24`.
[CI via Compose](https://github.com/UnicHeld/digitalmirror/actions/runs/37553831948)
passou em Python 3.11 e 3.13: configuração Compose, build das imagens dev/runtime,
formatter, lint, mypy, 40 testes e build sdist/wheel com artefatos publicados.
Logs confirmaram 40 testes em cada job. A leitura dos logs inicialmente foi
bloqueada pelo cache gh fora do sandbox; repetida após autorização e concluída.
Issue #2 e README do Project atualizados com os ADRs 008/009, CI e pendências.
US-02.1 concluída como comando/relatório; EP-02 continua In Progress, C0 pendente
e EP-03 no Backlog. CI sem sessão gráfica não valida as histórias de transição.

## Leitura real enviada pelo usuário — 06/10/2026 no calendário local

Evidência: resumo JSON fornecido pelo usuário após executar
`sh scripts/compose-desktop run --rm desktop` em seu terminal GNOME/X11.
Observação às 00:56:06 UTC de 07/10/2026 (21:56:06 em America/Sao_Paulo de
06/10/2026). Esta execução não foi iniciada pelo agente. Somente os resultados
técnicos agregados abaixo foram transcritos; o JSON de sessão não foi versionado.

| Fonte | Resultado informado |
| --- | --- |
| X11 foco, classe, PID, workspace e geometria | Cinco consultas disponíveis / read-ok |
| Idle X11 | Disponível / read-ok |
| XRandR | Disponível: dois monitores, um principal, janela focada atribuída a monitor |
| GNOME GetActive | Disponível / read-ok |
| logind LockedHint | Indisponível / missing-graphical-session-id |
| logind PrepareForSleep | Introspecção disponível / read-ok; nenhum ciclo observado nesta execução |
| graphical-session.target | Disponível / read-ok; não comprova autostart |

Resultado: **10 de 11 fontes disponíveis**, diagnóstico degraded esperado pelo
LockedHint ausente. Confirma leitura das fontes gráficas e autenticação dos mounts
desktop nessa execução. Não confirma a precisão da atribuição de monitor, foco,
lock ou continuidade após suspensão. Uma consulta GetActive bem-sucedida não prova
que seu valor acompanha bloqueio efetivo.

Uma amostra, intervalo nominal de 5s: janela medida de 0,181052s, latência p95
de 0,180950s, atraso de 0,000070s, CPU própria 0,008383s e de filhos 0,031358s.
CPU de 21,95% corresponde a essa janela curta, sem espera entre amostras; não é
CPU média do polling contínuo. RSS máximo próprio e do maior filho: 18.944 KiB
cada; não somar como memória simultânea. Startup, daemon Docker e watcher não
estão incluídos. Não há evidência suficiente para validar RNF de consumo ou 8h.

XDG_SESSION_ID ausente confirma que o comando não recebeu a variável; não prova
ausência da sessão no logind. O doctor atual só usa o ID explícito do ambiente e
não implementa descoberta de sessão. A origem exata da ausência no terminal não
foi diagnosticada. Consultar o logind por UID/sessão e validar a associação ao
DISPLAY seria uma mudança futura, exigindo decisão e testes; não exportar um ID
arbitrário nem recuperar ambiente de outros processos.

O processo do agente continua sem DISPLAY, XAUTHORITY, XDG_RUNTIME_DIR,
DBUS_SESSION_BUS_ADDRESS ou XDG_SESSION_TYPE. A disponibilidade no terminal do
usuário não transfere esse ambiente ao agente. Próximos ensaios via Compose:
polling de 12 amostras e watchers isolados com bloqueio/desbloqueio e
suspensão/retomada voluntários, conforme o protocolo. Precisão de foco,
LockedHint, dois perfis, autostart e C0 permanecem pendentes.

Validação desta atualização documental: `git diff --check` e
`sh scripts/compose run --rm dev` passaram (formatter, lint, mypy, 40 testes e
build sdist/wheel em Python 3.11). Não houve alteração de código ou novo ensaio
gráfico executado pelo agente.

## Polling e watcher GNOME enviados pelo usuário — 06/10/2026 local

Dois resultados fornecidos pelo usuário, executados via launcher desktop Compose.
As datas observed_at do polling são 07/10/2026 às 01:17:33 UTC (22:17:33 local)
e 01:19:29 UTC (22:19:29 local) para a amostra anterior ao watcher. O horário da
amostra não representa o encerramento do watcher. Nenhum JSON bruto foi versionado.

### Polling de 12 amostras a cada 5s

As dez fontes anteriormente disponíveis responderam read-ok nas **12 de 12
amostras**, sem falhas registradas. LockedHint permaneceu indisponível nas 12
amostras por missing-graphical-session-id; degraded continua esperado.

| Medida | Resultado informado | Avaliação |
| --- | --- | --- |
| Janela do polling | 55,202680s | Ensaio curto; não equivale a 8h |
| Latência p95 por ciclo | 205,275ms | Consulta termina bem antes do próximo intervalo nominal de 5s |
| Atraso p95 de início | 0,290ms | Abaixo de 1s nesta janela; não mede erro de foco |
| CPU própria / filhos | 0,113805s / 0,513613s | Aproximadamente 82% do tempo de CPU medido veio dos subprocessos |
| CPU média de um núcleo | 1,137% | Acima da meta RNF-03 de ≤1% em 0,137 ponto percentual |
| RSS máximo próprio | 19.112 KiB (18,66 MiB) | Abaixo de 100 MiB nesta janela; não valida estabilidade de 8h |
| Maior RSS máximo de filho | 19.112 KiB | Não somar como memória simultânea de todos os processos |

Avaliação: disponibilidade estável e agendamento com baixo atraso neste ensaio.
CPU ainda não atende à referência RNF-03 nessa janela, e não deve ser arredondada
para declarar aceite. O custo medido é do doctor com consultas auxiliares e
subprocessos, sem banco, bridge, API ou dashboard; também não inclui daemon Docker,
startup ou watcher. Conforme ADR-006 e contrato RNF, avaliar adaptadores com
conexões nativas antes da entrega, preservando o intervalo de 5s e sem pressupor
que remover subprocessos será suficiente. C0/RNF completas continuam pendentes.

### Watcher de 120s e ação manual Windows+L

O usuário relatou bloqueio manual com Windows+L. Em 120,003239s monotônicos, o
watcher GNOME recebeu true=2, false=2, **dois ciclos ordenados completos**, zero
duplicatas, zero fins sem início e nenhum início pendente; status observed e
cycle_status=complete. Isso confirma entrega real de ActiveChanged nessa sessão
durante o ensaio manual. A contagem de ações manuais ainda precisa ser correlacionada
com os dois ciclos: não assumir dois bloqueios efetivos nem duração ou latência de
bloqueio a partir do resumo. LockedHint/GetActive durante a tela bloqueada e
continuidade do serviço não foram comparados. US-02.2 permanece parcial.

PrepareForSleep: zero sinais/ciclos e cycle_status=no-events. Não houve relato
de suspensão nesse ensaio; resultado compatível com teste somente de bloqueio,
sem evidência de suspensão/retomada. Próximo ensaio: watcher separado com
suspensão e retomada voluntárias pelo GNOME; verificar um par true → false e
continuidade após retorno. Dois perfis, precisão de foco, autostart e C0 pendentes.

Os 30,689% de CPU da segunda saída se referem somente à amostra inicial de
197,212ms; **não** medem o custo do watcher de 120s. pending_validation é uma lista
estática de limites do spike, sem atualização automática pelo resumo de ciclos.

## Suspensão/retomada real enviada pelo usuário — 06/10/2026 local

Ensaio via `sh scripts/compose-desktop run --rm desktop digitalmirror doctor
--watch-seconds 180`. O usuário informou esperar cerca de 5s antes de suspender
pelo GNOME, permanecer aproximadamente 10s suspenso e, após retomar, aguardar o
JSON do mesmo comando. A amostra inicial foi observada às 01:36:33 UTC de
07/10/2026 (22:36:33 local de 06/10); não é o horário do fim do watcher.
Evidência fornecida pelo usuário; nenhum JSON bruto ou log de sessão versionado.

| Fonte | Sinais e ciclos informados | Resultado |
| --- | --- | --- |
| logind PrepareForSleep | true=1, false=1, complete_count=1 | observed / complete |
| GNOME ActiveChanged | true=1, false=1, complete_count=1 | observed / complete |

Ambas as fontes registraram zero duplicatas, zero fins sem início e nenhum início
pendente. Entrega de um par ordenado PrepareForSleep durante a ação voluntária
de suspensão/retomada **confirmada neste ensaio**. O processo concluiu a observação
e produziu JSON após o retorno, conforme relato do usuário. O par GNOME é
compatível com ativação/desativação da tela de bloqueio nessa sequência, mas não
determina ordem entre fontes nem comprova LockedHint ou momento do desbloqueio.

O watcher mediu 180,003885s monotônicos. No Linux, o relógio utilizado não inclui
tempo suspenso; aproximadamente 10s suspensos podem acrescentar tempo ao relógio
de parede. O resumo não mede a duração da suspensão: os 10s são estimativa manual.
A retomada até a saída final não comprova revalidação de X11, GNOME GetActive,
monitores ou estado gráfico: o polling ocorreu somente antes do watcher. Não há
coletor persistente instalado para validar intervalos/gaps após suspensão.

Dez fontes disponíveis na amostra inicial; LockedHint segue indisponível por
missing-graphical-session-id e mantém degraded/1. Os 24,558% de CPU referem-se
apenas à amostra inicial de 161,964ms, sem incluir watcher/suspensão. Os resultados
de CPU média válidos para polling continuam os do ensaio de 12 amostras acima.
pending_validation permanece estática e não invalida o par real agora observado.

US-02.2: ação manual de suspensão/retomada e entrega do par observadas; correlação
dos dois ciclos Windows+L anteriores, comparação LockedHint/GetActive e
revalidação das fontes após retomada continuam pendentes. US-02.3/04, precisão
de foco, autostart, perfis, RNF de 8h e C0 não encerrados por esse ensaio.

## Implementação da etapa 1 — sessão validada e revalidação (ADR-010)

O doctor agora valida sessão explícita ou User.Display do UID real do host antes
de LockedHint. Verifica Id/UID/tipo/classe/localidade/DISPLAY por JSON tipado do
busctl. Não enumera sessões, lê ambiente de processos ou reutiliza candidato após
falha. Launcher preserva UID do host antes de mapeá-lo para 0 no namespace rootless.

Watcher recebe consultas GetActive/LockedHint a cada 5s, contagens de estados e
comparações sequenciais. Cada par PrepareForSleep true → false provoca consultas
novas a todas as fontes; há também post_watch_checks no fim. Falhas de monitor,
consulta de estado ou revalidação mantêm degraded mesmo após recuperação. Custos
dessas consultas não entram nas medições de polling anteriores ao watcher.

Validações locais executadas via Compose/Python 3.11:

- Formatter Ruff, lint, mypy estrito, **53 testes** e build sdist/wheel passaram.
- Treze novos testes cobrem identidade/proveniência, candidato incorreto, tipos
  inválidos, falha sem fallback, estados divergentes/indisponíveis, recuperação,
  revalidação somente por par ordenado e falha final com retorno 1.
- Imagens dev/runtime reconstruídas; sintaxe shell e git diff --check passaram.
- Configuração desktop com variáveis sintéticas e ID vazio válida; UID real do
  host preservado junto de 0:0 interno, mounts read-only/capabilities removidas,
  nenhuma porta publicada. Config sem variáveis gráficas recusou interpolação;
  repetida com fixture sintética, sem criar sessão ou usar credenciais de terceiros.
- JSON busctl de GetUser/User.Display e propriedades selecionadas lido no D-Bus
  real dentro do runtime; somente formas/tipos inspecionados, sem publicar dados.
- Resolver no runtime com UID real e DISPLAY sintético incorreto rejeitou candidato
  com session-identity-mismatch; não consultou LockedHint como sessão validada.
- Runtime somente com D-Bus de sistema: watcher de 2s conectado ao logind, zero
  sinais/ciclos; estados de lock indisponíveis e post_watch_status=degraded, fonte
  PrepareForSleep consultável após watcher. Não confirma suspensão ou sessão gráfica.
- Launcher real do agente continua recusando ausência de GNOME/X11 com código 2.

Falhas iniciais de import/linha longa e captura de variáveis de teste no lint,
invariância de dict na tipagem e iteração de chaves no teste de privacidade foram
corrigidas; checks repetidos com sucesso. Nenhuma nova dependência de produção.
Evidências gráficas anteriores permanecem históricas; ainda aguardamos executar
a versão ADR-010 no terminal do usuário. Não afirmar 11 fontes disponíveis,
confiabilidade GetActive/LockedHint, recursos RNF ou C0 com base nos testes sintéticos.

## Primeiro resultado real do ADR-010 — encerramento da sessão de 06/10/2026

O usuário executou `sh scripts/compose-desktop run --rm desktop` no terminal real.
Observação às 02:16:59 UTC de 07/10/2026 (23:16:59 local de 06/10), após publicação
do commit `086e553`. Evidência fornecida pelo usuário, sem JSON bruto versionado.

Dez de onze fontes read-ok: foco/classe/PID/workspace/geometria/idle X11, XRandR
com dois monitores (um principal, janela atribuída), GNOME GetActive=false,
introspecção PrepareForSleep e alvo gráfico. LockedHint **não consultado como
sessão validada**: logind-lock=unavailable, reason=session-identity-mismatch,
session_validated=false e resolved_from_user_display=false. Diagnóstico degraded.

Avaliação: fontes previamente disponíveis seguem funcionando; resolução não
atingiu aceite. O código rejeitou o candidato por ao menos uma diferença entre
Id/UID/Type/Class/Remote/Display. O motivo agregado não informa qual atributo.
O campo resolved_from_user_display=false em falha não prova uso de ID explícito,
pois falhas de qualquer caminho retornam o valor padrão. Não atribuir causa sem
instrumentação adicional; não afrouxar validação para transformar saída em available.

Uma amostra: janela 0,224802s, latência p95 0,224669s, atraso 0,000066s, CPU própria
0,012735s e de filhos 0,052519s; 29,028% de um núcleo nessa janela curta, sem espera
de polling. RSS próprio e maior filho 19.364 KiB cada. Não comparar esse percentual
com polling de 12 amostras nem RNF de 8h. Sem watcher, não testa comparação de
lock, revalidação na retomada ou post_watch_checks da implementação nova.

Implementação ADR-010 teve [CI via Compose](https://github.com/UnicHeld/digitalmirror/actions/runs/37560776472)
aprovada em Python 3.11 e 3.13; 53 testes/checks/build passaram localmente.
O usuário encerra esta sessão e retorna no dia seguinte. Esta atualização somente
registra a evidência e a retomada; nenhuma correção de código ou novo ensaio gráfico.
Primeiro passo ao retomar: motivos de divergência e proveniência sanitizados,
regressões, investigação da associação real e repetição do doctor; depois watchers
de lock/retomada e etapas de foco/perfis/login/logout. Handoff em docs/cli-handoff.md.
EP-02 In Progress, US-02.2 parcial, C0 pendente e EP-03 Backlog.

## Retomada de 07/10/2026 — instrumentação de identidade

Implementada extensão sanitizada do ADR-010, mantendo seleção do candidato,
validação e reason=session-identity-mismatch. logind-lock.details informa
candidate_source inclusive em falhas, seis comparações booleanas após parse
tipado completo, categoria de Display e relação entre UID interno e UID do host.
Não imprime valores de identidade nem acrescenta consultas/mounts. Regressões
cobrem divergências individuais/múltiplas, Display vazio/não local/outro servidor,
falhas nos estágios de consulta, tipos inválidos, privacidade e UID interno
rootless. O caminho User.Display conserva proveniência também após rejeição.

Ambiente do agente: Docker rootless, sem variáveis de sessão gráfica herdadas.
A captura fornecida pelo usuário informa Debian 12/GNOME 43.9 e duas resoluções;
não permite determinar qual atributo divergiu. Nenhuma nova evidência de
identidade logind, LockedHint real, lock/unlock ou retomada foi recebida nesta etapa.

Validação em Docker Compose/Python 3.11:

- `sh scripts/compose run --rm dev ruff format .`: executado, um arquivo formatado.
- `sh scripts/compose run --rm dev`: formatter check, lint, mypy, 57 testes e
  sdist/wheel aprovados; repetido na imagem reconstruída, também aprovado.
- Primeiras tentativas dos checks pararam em lint (duas capturas de variáveis
  nos testes) e mypy (inferência do dict de monitores ao ampliar details para enums);
  falhas corrigidas antes da aprovação.
- `sh scripts/compose build dev desktop`: primeira tentativa bloqueada pelo
  sandbox ao escrever metadados de Buildx em ~/.docker; repetição autorizada
  concluiu ambas as imagens.
- `sh scripts/compose run --rm dev digitalmirror doctor` e
  `sh scripts/compose --profile desktop run --rm desktop`: sem mounts de sessão,
  retornaram degraded/código 1 esperado; logind-lock sem sessão X11 confirmada,
  session_validated=false e candidate_source=not-attempted. Confirmam execução
  da extensão na CLI/imagem, sem validar as fontes reais ou consumo contínuo.

Pendência: doctor simples no terminal GNOME/X11 e análise do objeto logind-lock
antes de corrigir associação. Depois, watchers separados de lock (120s, ≥15s
bloqueado/desbloqueado) e suspensão/retomada (180s), conforme protocolo. Sem nova
CI remota ou ensaio gráfico deste incremento; alterações locais sem commit/push.
EP-02 e C0 continuam pendentes; EP-03 não iniciado.

## Doctor instrumentado real — 07/10/2026, 19:32 local

Resultado informado pelo usuário de `sh scripts/compose-desktop run --rm desktop`,
observed_at=22:32:01.948195 UTC (19:32:01 local). Sem JSON bruto versionado.

Dez fontes read-ok; GNOME GetActive=false. XRandR informa um monitor, principal,
com janela atribuída. Evidências anteriores de dois monitores são preservadas;
não inferir causa da diferença nem configuração física pela captura anterior.

logind-lock indisponível por session-identity-mismatch, com proveniência
candidate_source=user-display. Id, UID do host, tipo x11, classe user e Remote=false
confirmados; somente identity_display_matches=false, com session_display_status=empty.
Portanto, a comparação que rejeitou o candidato foi Session.Display vazio; não
foi demonstrado um nome de servidor diferente. Não houve consulta de LockedHint
de sessão validada. resolved_from_user_display=false conserva semântica de sucesso
e não contradiz a proveniência user-display.

process_uid_is_root=true e host_uid_matches_process_uid=false são coerentes com
o rootless do launcher; identity_uid_matches=true confirma comparação com o UID
real fornecido. Não há evidência de uso incorreto do UID interno para associação.

Uma amostra, janela 0,172335s, latência p95 0,172185s, atraso 0,000068s; CPU própria
0,015008s e filhos 0,067156s, 47,677% de um núcleo nessa janela sem espera de polling.
RSS próprio e maior filho 19.224 KiB cada. Não é CPU média contínua nem soak RNF.
Sem watcher nesta saída, não valida transições, comparação ou revalidação.

Verificação documental: o [manual logind do Debian 12](https://manpages.debian.org/bookworm/systemd/org.freedesktop.login1.5.en.html)
distingue User.Display (ID/path de sessão primária) de Session.Display (nome X11).
SetDisplay é atribuição do controlador da sessão; LockedHint reflete hint informado
pelo desktop. A documentação não determina a causa upstream da propriedade vazia
neste host. Não atribuir a PAM, GDM ou Docker sem investigação adicional.

Decisão no ADR-010: preservar validação e fonte logind-lock indisponível;
continuar pelo fallback GNOME já implementado. Não alterar sistema/login ou
fabricar Session.Display. Próximo aceite: um bloqueio/desbloqueio manual correlacionado
a ciclo GNOME e consultas true/false, seguido de suspensão/retomada com revalidações.
comparison_counts.unavailable e diagnóstico degraded são esperados; comparação
com LockedHint continua não validada. Falha GNOME conserva bloqueio desconhecido.

Esta continuação alterou somente documentação (ADR-010, spec/plan/tasks, protocolo,
relatório e handoff); código/testes preservados. Checks Python/Compose de 57 testes
pertencem ao incremento anterior; não repetidos nesta atualização documental.
Watchers reais novos e CI remota pendentes; sem commit/push. C0 não atingido.

## Watcher instrumentado de lock — 07/10/2026, 20:01 local

Resultado fornecido pelo usuário de
`sh scripts/compose-desktop run --rm desktop digitalmirror doctor --watch-seconds 120`.
observed_at=23:01:16.208311 UTC (20:01:16 local) identifica a amostra inicial,
não o fim do watcher. Duração monotônica observada: 120,003736s.
Resumo sanitizado, sem JSON bruto ou história pessoal versionados.

GNOME ActiveChanged recebeu true=1 e false=1: um ciclo completo, nenhum início
pendente, zero fins sem início e zero duplicatas. Status observed/cycle_status=complete,
sem falha de conexão reportada. GetActive foi consultado 24 vezes com read-ok
24/24; true=7 e false=17. As duas condições foram amostradas, mas as contagens não
medem duração de bloqueio e não comprovam a ação real sem relato do usuário.

logind-lock indisponível 24/24 por session-identity-mismatch; comparison_counts
unavailable=24. Na amostra inicial e post_watch_checks, o candidato user-display
passou em Id/UID/Type/Class/Remote, mas Session.Display continuou vazio. Nenhuma
comparação com LockedHint foi validada. O diagnóstico e state_observation
permanecem degraded pela fonte indisponível esperada.

post_watch_checks: dez fontes read-ok, incluindo foco/classe/PID/workspace/
geometria/idle X11, GNOME=false, introspecção PrepareForSleep e alvo gráfico.
XRandR com um monitor principal e janela atribuída. A leitura ao fim comprova
disponibilidade naquele instante; não demonstra foco contínuo durante bloqueio.
post_watch_status=degraded somente por logind-lock indisponível.

PrepareForSleep sem eventos, zero ciclos e cycle_status=no-events;
resume_revalidation.confirmed_signal_pairs=0, sem contagens de revalidação.
Esse ensaio não valida suspensão/retomada.

Medição inicial de uma amostra: janela 0,139930s e CPU de 48,211% de um núcleo;
RSS próprio e maior filho 19.232 KiB cada. Não inclui custo dos 120s do watcher
nem constitui CPU média de polling/soak.

Aceite parcial: ciclo, estados true/false e leitura final coerentes com o protocolo
de fallback GNOME. Falta confirmar que houve exatamente um bloqueio efetivo e um
desbloqueio manual, ≥15s em cada estado, terminando desbloqueado. Confirmação
solicitada; não inferir as ações pelo comando ou pelos sinais. Próximo ensaio:
suspensão/retomada separada de 180s, com relato e conferência de resume_revalidation
e post_watch_checks. Nenhuma fonte logind foi liberada nem critério alterado.

Atualizados relatório, handoff e checklist; código preservado. Validação desta
atualização somente documental: git diff --check. Checks Python e build não
repetidos; 57 testes aprovados anteriormente pertencem à instrumentação.
CI remota deste incremento não executada; sem commit/push. C0 e EP-02 pendentes.

## Relato de lock e watcher de suspensão — 07/10/2026, 20:05 local

O usuário respondeu afirmativamente sobre o primeiro ensaio: uma ação, espera de
aproximadamente 15s, retorno e espera pela saída. O atalho foi descrito como Ctrl+L.
Esclarecimento solicitado sobre tela de bloqueio GNOME/autenticação versus limpeza
do terminal. O relato não será reescrito como Windows+L; aceite do fallback de lock
permanece pendente dessa distinção. Ciclo e consultas do ensaio anterior preservados.

Para o segundo ensaio, o usuário informou suspensão manual, espera de cerca de 15s
e retomada, usando
`sh scripts/compose-desktop run --rm desktop digitalmirror doctor --watch-seconds 180`.
observed_at=23:05:42.384198 UTC (20:05:42 local) é timestamp da amostra inicial.
Duração monotônica 180,006353s; aproximadamente 15s suspenso vêm do relato, não
do watcher. O comando produziu a saída após retorno. Sem JSON bruto versionado.

PrepareForSleep e GNOME ActiveChanged: cada stream recebeu true=1/false=1, um ciclo
completo, zero duplicatas/fins sem início e nenhum início pendente. Status observed
e cycle_status=complete nos dois streams, sem falha de conexão reportada.
Não inferir ordem entre streams, instante/duração de bloqueio ou bloqueio automático
na retomada sem relato: o resumo só preserva a ordem interna de cada fonte.

GetActive read-ok em 35/35 consultas, true=2/false=33; logind-lock indisponível
35/35 por session-identity-mismatch, comparison_counts.unavailable=35. A consulta
inicial e final confirmam novamente cinco atributos de identidade, mas Display
vazio impede associação. Sem LockedHint validado nem comparação de fontes.

resume_revalidation.confirmed_signal_pairs=1 confirma acionamento da consulta
de todas as fontes após par PrepareForSleep. Resultado dessa leitura:

| Fontes | Na revalidação de retomada | Ao fim do watcher |
| --- | --- | --- |
| x11-focus | available, no-focused-window | available, read-ok |
| window-class/PID/workspace/geometry | unavailable, no-focused-window | available, read-ok |
| idle/XRandR/GNOME/PrepareForSleep/alvo gráfico | available, read-ok | available, read-ok |
| logind-lock | unavailable, session-identity-mismatch | unavailable, mesmo motivo |

A ausência de janela focada é resposta válida do adaptador X11, não timeout,
erro de conexão ou reutilização de foco antigo. O código torna propriedades da
janela indisponíveis nessa condição e conserva degraded em state_observation mesmo
após recuperação. É compatível com uma transição de retomada; o resumo não permite
afirmar se a leitura ocorreu durante tela bloqueada ou outra etapa da transição.
Na coleta futura, ausência de app conserva app desconhecido sem invalidar por si
um estado de sessão confirmado; não inventar presença quando lock/idle faltarem.

Ao fim, dez fontes read-ok, incluindo as quatro propriedades recuperadas;
GNOME=false, um monitor principal com janela atribuída. post_watch_status=degraded
por logind-lock indisponível. Confirma recuperação das leituras nesse instante,
sem medir latência da recuperação ou precisão de foco. Não apagar as indisponibilidades
intermediárias nem repetir ensaio apenas para obter status available.

Medição inicial de uma amostra: janela 0,131035s, CPU de 47,408% de um núcleo e
RSS próprio/maior filho de 19.204 KiB cada. Exclui os 180s do watcher e tempo suspenso;
não comprova RNF de CPU/memória contínua.

Aceite: suspensão/retomada manual correlacionadas ao par logind, revalidação
acionada e leituras recuperadas ao fim. Lock GNOME aguarda esclarecimento do relato;
comparação LockedHint permanece indisponível. Depois do aceite do fallback, seguir
precisão de foco/monitores, perfis e login/logout/instância única; C0 não atingido.

Alteração somente documental em relatório, handoff e checklist; código preservado.
git diff --check executado; checks Python/build não repetidos, CI remota pendente.
Sem commit/push; EP-02 permanece In Progress e EP-03 não iniciado.

## Esclarecimento e aceite da etapa 1 — 07/10/2026

O usuário corrigiu o atalho informado: Windows+L para bloquear. A correção,
junto da resposta afirmativa anterior de uma ação e espera de aproximadamente
15s antes de retornar, permite correlacionar o único ciclo GNOME do ensaio
isolado de 120s ao bloqueio/desbloqueio manual. Estados true/false amostrados e
leitura final false sustentam o aceite do fallback nesse host, sem medir duração.

Etapa 1 aceita no escopo do spike: bloqueio/desbloqueio GNOME e suspensão/retomada
manual com par PrepareForSleep, revalidação acionada e recuperação das leituras
ao fim. A ausência imediata de foco/propriedades da janela na retomada permanece
registrada; não reutilizar app nem tratá-la como prova de falha X11 ou de duração.
LockedHint continua indisponível por Session.Display vazio, sem comparação entre
fontes ou mudança de critério. Essa limitação deve entrar na decisão final C0.

Próximas etapas: precisão de foco/monitores, correlação de duas janelas/perfis por
extensão mínima e prova de login/logout/instância única. RNF de CPU (1,137% no
polling histórico) e soak de 8h continuam pendentes. Não encerrar EP-02 ou iniciar
EP-03 antes de C0. Atualizados ADR-010, handoff, checklist e relatório; somente
documentação nesta confirmação, sem repetir checks Python/build ou fazer commit/push.

## Consultas complementares no host — 07/10/2026, 20:19–20:23 local

Evidência fornecida pelo usuário, executada diretamente no terminal do host;
não é nova medição via Docker. Registrar somente relações e resultados, sem
IDs/UID, usuário, seat/TTY, DISPLAY, nomes de saídas ou configuração pessoal.

- Ambiente do terminal confirma DISPLAY local preenchido e tipo x11.
- Listagem manual mostrou uma sessão; User.Display indicou essa mesma sessão.
  A seleção por listagem não será incorporada ao coletor; manter GetUser/User.Display.
- show-session self falhou no host: chamador não pertence a sessão conhecida.
  Logo, essa falha específica também ocorre fora do contêiner. Não concluir que
  a sessão gráfica inexiste; ela foi consultada explicitamente depois.
- Consulta explícita da sessão indicada retornou LockedHint=no. A propriedade
  foi acessível no host naquele instante; o doctor permanece impedido de consultá-la
  pelo critério de associação Session.Display, não por erro de acesso já observado.
  Essa única leitura não valida atualização durante bloqueio/desbloqueio, leitura
  no contêiner nem identidade dessa sessão em relação ao servidor X11.
- xrandr --listmonitors informou dois monitores definidos, um principal, com
  resoluções distintas. Doctor usa --listactivemonitors; consultas ocorreram em
  instantes diferentes e filtram conjuntos distintos. Não atribuir a discrepância
  a Docker sem comparação do mesmo comando/servidor/configuração no mesmo período.
- wlr-randr não foi encontrado. O alvo validado é X11; essa ausência não invalida
  as leituras XRandR já realizadas e não exige adicionar ferramenta ao projeto.

Uma hipótese para self indisponível é processo iniciado pelo systemd user manager,
fora de uma session scope. O [manual sd_pid_get_session do Debian 12](https://manpages.debian.org/bookworm/libsystemd-dev/sd_pid_get_session.3.en.html)
documenta esse cenário para processos de usuário, inclusive GUI por ativação D-Bus.
É hipótese, não origem do terminal comprovada. Associação por PID pode falhar pelo
mesmo motivo; não tratá-la como alternativa garantida nem recuperar ambiente de processos.
O [manual XRandR](https://manpages.debian.org/bookworm/x11-xserver-utils/xrandr.1.en.html)
distingue monitores definidos de ativos.

Esses comandos não consultaram Session.Display explicitamente; a evidência de valor
vazio continua sendo a resposta tipada do doctor. Conhecer DISPLAY no terminal ou
ver apenas uma sessão não substitui a comprovação exigida no ADR-010. Possibilidade
de obter LockedHint confirmada no host; associação e correlação durante lock ainda
pendentes para essa fonte. Fallback GNOME e aceite anterior preservados.

Atualizados relatório, handoff e checklist, sem código ou mudança de critérios.
git diff --check executado; testes/build não repetidos. Sem commit/push ou nova CI.
