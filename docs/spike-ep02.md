# EP-02 — Protocolo de viabilidade passiva

Escopo M0: disponibilidade das fontes e custo básico. O programa não instala
serviço, não simula inputs, não muda foco e não solicita bloqueio/suspensão.
Ensaios reais exigem ações voluntárias do usuário na sessão GNOME/X11.
Contrato em [spec](../specs/002-session-collector/spec.md), decisões em
[ADR-006](adr/006-passive-doctor.md). Evidência desta execução em
[relatório](spike-ep02-report.md).

## Preparação no alvo

Host: Docker Engine local Linux/Compose v2+, acessível ao usuário da sessão.
Python/ferramentas de diagnóstico ficam na imagem; sempre usar Compose, sem venv.
Construa as imagens e execute no terminal Debian 12/GNOME/**X11** real:

```bash
sh scripts/compose build dev desktop
sh scripts/compose-desktop run --rm desktop
```

O Dockerfile instala na imagem: `xprop`, `xdotool`, `xrandr`, `xprintidle`,
`gdbus`, `busctl`, `systemctl` e `stdbuf` para observar eventos. No Debian vêm de
`x11-utils`, `xdotool`, `x11-xserver-utils`, `xprintidle`, `libglib2.0-bin`,
`systemd` e `coreutils`. Não instalar esses pacotes ou Python diretamente no host.
O launcher monta sockets X11/D-Bus e Xauthority somente leitura, preserva o
usuário e valida os caminhos antes da chamada a Compose. Em rootless, UID 0
interno corresponde ao usuário não privilegiado do host. Rootless exige ensaio
de autenticação das fontes; leitura de logind via socket foi verificada nesse modo.
Hostname do host é fornecido transitoriamente para cookies Xauthority FamilyLocal;
não versionar configuração resolvida contendo paths/hostname da sessão.
Não fixe DISPLAY, XAUTHORITY, session ID ou endereço D-Bus. Uma sessão Wayland
não valida o alvo X11. Código 1 representa diagnóstico degradado; 2, argumento inválido.
XDG_SESSION_ID não é obrigatório no terminal. Conforme
[ADRs 009/010](adr/010-session-validation-and-watch-checks.md), ausência desse ID
permite consultar somente User.Display do UID real do host fornecido pelo launcher.
Antes de LockedHint, validar ID/UID, tipo x11, classe user, sessão local e DISPLAY.
Falha mantém logind-lock indisponível; o launcher não bloqueia as consultas
GNOME/X11 ou PrepareForSleep por esse motivo. Não escolher um ID da
primeira sessão listada, de SSH/TTY ou de outro processo; ID explícito só pode
corresponder à sessão gráfica observada. As demais verificações permanecem obrigatórias.
O [pam_systemd do Debian 12](https://manpages.debian.org/bookworm/libpam-systemd/pam_systemd.8.en.html)
inicializa XDG_SESSION_ID no login. Ausência no terminal indica que essa variável
não chegou ao comando; a causa específica exige diagnóstico e não implica ausência
da sessão no logind. O doctor aceita ID explícito validado ou User.Display validado;
não busca outro candidato se o explícito estiver incorreto. O UID interno 0 em
rootless não identifica usuário do host; DIGITALMIRROR_HOST_UID vem de id -u.
XDG_RUNTIME_DIR é compartilhado entre sessões do mesmo usuário e sozinho não
identifica a sessão gráfica. Não alterar PAM ou exportar ID arbitrário para
transformar o diagnóstico em available.
Sem sessão, `sh scripts/compose run --rm dev digitalmirror doctor` continua
funcionando e identifica fontes ausentes; não é ensaio da sessão real. Nenhum
serviço usa privileged, Docker socket, home completo ou xhost +.
O JSON mostra fontes, motivos/fallbacks e pendências sem título, app, PID, hostname
ou nome de monitor. Mesmo código 0 não encerra os ensaios abaixo.

## Investigar session-identity-mismatch

Após reconstruir as imagens, repetir o doctor simples no terminal GNOME/X11 com
o ambiente original. Analisar o objeto `checks` cuja `source` é `logind-lock`.
Compartilhar esse objeto sanitizado, sem saída bruta de busctl, `env`, cookies
ou configuração resolvida do Compose.

`candidate_source` identifica `explicit-session-id` (GetSession), `user-display`
(GetUser → User.Display) ou `not-attempted` (pré-condição rejeitada). Preserva a
proveniência mesmo em falha; `resolved_from_user_display=false` sozinho continua
sem informar o caminho tentado. Os seis booleans abaixo só aparecem após parse
completo das propriedades, e cada `false` identifica uma divergência:

| Campo | Comparação exigida |
| --- | --- |
| `identity_id_matches` | Id igual ao candidato fornecido/indicado |
| `identity_uid_matches` | User/UID igual ao UID real fornecido pelo launcher |
| `identity_type_x11` | Type igual a x11 |
| `identity_class_user` | Class igual a user |
| `identity_remote_false` | Remote igual a false |
| `identity_display_matches` | Display local igual ao servidor observado, ignorando screen |

`session_display_status=empty` identifica propriedade vazia;
`nonlocal-or-invalid`, formato que não atende ao DISPLAY local; `local`, formato
local válido, que ainda pode apontar para servidor diferente. Ausência dos campos
de comparação significa que não chegaram a ser calculados; não implica aprovação.

Complemento ADR-011: com Display exatamente vazio e cinco outros critérios
válidos, o doctor tenta associação por VT, seat0 ativo e releituras. Nesse sucesso,
identity_display_matches permanece false, session_display_status=empty e
session_validated=true com session_association_source=x11-vt. Não foi preenchido
Display nem ignorada divergência. Com Display correspondente, associação
session-display; em falha, not-validated. vt_association_attempted e comparações
identity_vt_*/identity_seat_*/identity_session_active/identity_revalidation_matches
indicam etapas já lidas, sempre sem valores pessoais. Conferir os critérios do
[ADR-011](adr/011-empty-display-vt-association.md); não concluir sucesso de campo
ausente ou booleano isolado. Fonte disponível permite consulta/comparação de
LockedHint, mas seu comportamento precisa de ensaio manual de bloqueio/retomada.

No rootless detectado pelo launcher, `process_uid_is_root=true` e
`host_uid_matches_process_uid=false` são esperados: UID 0 interno não substitui
o UID real na associação. `identity_uid_matches` deve continuar true. Esses
booleans não identificam por si o modo do daemon. Registrar apenas suas relações,
sem números. Não tratar DISPLAY vazio ou outra divergência como justificativa
automática para afrouxar o ADR-010; qualquer novo critério exige evidência e ADR/spec.

Só depois da associação válida, ou decisão explícita e fundamentada de fallback
GNOME, prosseguir aos ensaios separados de lock (120s) e suspensão/retomada (180s).

Decisão histórica no ADR-010 em 07/10/2026: o candidato real passou em cinco
comparações, mas Session.Display veio vazio. Preservar logind-lock indisponível;
ensaiar o fallback GNOME existente conforme sequência abaixo. Não chamar SetDisplay
ou alterar o login. Comparação com LockedHint permanece não validada.
Complemento vigente ADR-011: tentar a associação adicional por VT/seat/atividade
e releituras quando Display for vazio; se falhar, seguir esse fallback. Primeiro
receber doctor simples reconstruído antes de ensaiar comparação de lock/retomada.

1. Executar `sh scripts/compose-desktop run --rm desktop digitalmirror doctor --watch-seconds 120`.
   Aguardar cerca de 5s para conectar, manter desbloqueado por ≥15s, bloquear
   manualmente uma vez (Windows+L), manter bloqueado por ≥15s, desbloquear e
   aguardar a saída. Relatar que houve uma ação de bloqueio e uma de desbloqueio
   efetivos, se foram exatamente essas as ações realizadas.
2. Conferir um ciclo GNOME completo, sem duplicatas/fins sem início/início pendente,
   contagens true e false em source_state_counts.gnome-lock, conexão sem falha e
   post_watch_checks coerente com a tela desbloqueada. Contagens não fornecem
   duração; tempos e ações vêm do relato manual.
3. Depois do ensaio de lock, executar separadamente
   `sh scripts/compose-desktop run --rm desktop digitalmirror doctor --watch-seconds 180`.
   Aguardar conexão, suspender e retomar manualmente pelo GNOME. Relatar as ações
   e o bloqueio automático, caso ocorra; conferir par PrepareForSleep,
   resume_revalidation e post_watch_checks de todas as fontes.

Nesses ensaios, logind-lock indisponível, comparison_counts.unavailable e
status degraded/código 1 são esperados. Não interpretar isso como falha automática
do ensaio GNOME nem como concordância GetActive/LockedHint. Falhas de outras fontes
e divergência entre GNOME/ação manual continuam impeditivas. Sem validação real
do fallback, não liberar C0 ou a classificação do futuro coletor.

## Polling, monitores e precisão

### Investigação passiva de Display vazio por VT

Com Display vazio também confirmado no host, comparar o VT da sessão indicada
por User.Display com o VT publicado pelo servidor Xorg. No terminal GNOME/X11:

```bash
digitalmirror_session_candidate=$(loginctl show-user "$(id -u)" --property=Display --value)
loginctl show-session "$digitalmirror_session_candidate" --all --property=Display --property=VTNr --property=Service
xprop -root XFree86_VT
sh scripts/compose-desktop run --rm desktop xprop -root XFree86_VT
```

Prosseguir somente se User.Display indicar candidato não vazio; não substituir
por ID fixo, self ou listagem. Não exportar XDG_SESSION_ID nem alterar DISPLAY.
Essa consulta de propriedades no host não é validação do doctor/LockedHint; não
altera sessão. Compartilhar resultados ou relações, sem nomes/cookies/ambiente.
XFree86_VT não tem underscore inicial e é propriedade da raiz, não de uma janela.
Falta da propriedade ou VT diferente impede usar essa hipótese como associação.
Valores iguais são evidência para avaliar critério adicional, ainda exigindo
identidade/localidade, seat/atividade, revalidação e ADR/spec antes do código.
Não chamar SetDisplay/TakeControl ou alterar login para fabricar metadado.

### Comparar monitores no host e no contêiner

Antes de repetir polling, comparar as mesmas consultas no mesmo terminal
GNOME/X11, sem conectar/desconectar telas ou mudar configuração entre comandos:

```bash
xrandr --listmonitors
xrandr --listactivemonitors
sh scripts/compose-desktop run --rm desktop xrandr --listmonitors
sh scripts/compose-desktop run --rm desktop xrandr --listactivemonitors
```

São consultas passivas. Não alterar DISPLAY, usar sudo, instalar wlr-randr ou
configurar saídas para produzir um resultado esperado. Informar se as duas telas
estavam ligadas e exibindo o desktop em modo estendido ou espelhado. Para revisão,
compartilhar somente a primeira linha `Monitors: N` de cada comando e eventuais
erros; nomes de saídas, dimensões e posições não precisam ser publicados.

Comparar host/contêiner separadamente para cada opção. Se houver divergência
entre comandos equivalentes, investigar acesso/ambiente antes de atribuir a
diferença à opção active ou ao parser. O parser do doctor exige que a contagem
do cabeçalho corresponda a todas as linhas; não ignora um monitor silenciosamente.
Resultados iguais só confirmam a contagem naquele instante. Não comprovam
atribuição ao monitor secundário, precisão de foco ou comportamento após mudanças.

Depois da comparação, repetir a medição abaixo mantendo a configuração das telas.
O relatório mostra os detalhes de monitores somente da última amostra; suas
contagens de disponibilidade não demonstram que a topologia foi constante.

### Disponibilidade e custo básico de polling

```bash
sh scripts/compose-desktop run --rm desktop digitalmirror doctor --samples 12 --interval 5
```

São 12 ciclos finitos (aproximadamente 55s + custo da última consulta). A medição
inclui CPU do processo e filhos, latência p95, atraso p95 e RSS máximo; RSS de
filhos é o maior filho, **não** soma simultânea. CPU usa tempo de execução do loop,
incluindo esperas; startup e watcher são externos à janela medida. Uma amostra
única não representa CPU média de polling. Não comparar com soak RNF de 8h.
Por exemplo, 21,95% em uma única janela de aproximadamente 181ms descreve o custo
daquela consulta, sem os intervalos de espera de um polling contínuo.

Verifique count/primary_count com uma e duas telas, geometria negativa e janela
no monitor secundário. Mude o foco manualmente entre terminal, IDE e navegador,
sem comandos de mudança de foco. O doctor só comprova disponibilidade, não registra
transições de app; precisão nominal de até 5s é proposta, não medida por esse JSON.
O futuro adaptador precisa de ensaio cronometrado de transições antes do aceite.
Na extensão do ADR-005, `focused_window_on_primary` aparece somente com janela
atribuída e principal único. true indica principal, false outro monitor; ausência
significa classificação desconhecida. É detalhe apenas da última amostra, sem
nomes ou geometria e sem alterar foco global. Leituras sequenciais podem observar
transições; para testar atribuição, manter uma janela inteiramente em uma tela.

Após reconstruir as imagens, executar doctor simples com terminal estável no
monitor secundário. Para consultar uma janela na tela principal sem trazer o
terminal ao foco durante a leitura, iniciar o comando com atraso:

```bash
sleep 10
sh scripts/compose-desktop run --rm desktop
```

Colar as duas linhas juntas no terminal; durante os 10s, selecionar manualmente
a janela na tela principal e mantê-la focada até a consulta terminar. Não minimizar
o terminal nem usar comando que altere foco. Conferir count=2, primary_count=1,
focused_window_assigned=true e focused_window_on_primary=false/true nos ensaios
secundário/principal respectivamente, se as telas mantiverem esses papéis.
O shell inicia Compose após o atraso; aguardar também a criação do contêiner.
Comparar os resultados com o relato manual, sem inferir crédito de app/aba ou
erro temporal de transições. Não repetir polling longo apenas para esse booleano.

Falha de app não deve tornar a sessão automaticamente UNKNOWN; falta de sinais
críticos de lock/idle deve. Desconexões não reutilizam o último foco.

## Bloqueio/desbloqueio e suspensão/retomada

```bash
sh scripts/compose-desktop run --rm desktop digitalmirror doctor --watch-seconds 300
```

O polling inicial termina antes da observação. Depois dele, bloqueie/desbloqueie
manualmente e, em outro ensaio, suspenda/retome pelo GNOME. O observador permanece
passivo, sem inhibitors ou chamadas de alteração de sessão. A duração é monotônica;
tempo suspenso não entra no deadline Linux e a execução termina após a retomada.
Para um ensaio curto de bloqueio, use `--watch-seconds 120`, aguarde cerca de 5s
para conexão dos watchers, bloqueie/desbloqueie uma vez e espere o JSON final.
Execute a suspensão em uma janela separada; bloqueio automático na retomada pode
também produzir sinais GNOME e deve ser identificado no relato manual.

Compare GetActive/ActiveChanged com o bloqueio real; uma tela de proteção pode
não ter a mesma semântica de bloqueio. Valide também LockedHint da mesma sessão
com consultas durante o ensaio. No ADR-010, o watcher faz essas consultas a cada
5s em `event_watch.state_observation.lock_polling`. Para comparação, mantenha a
tela bloqueada por pelo menos 15s e desbloqueada por pelo menos 15s. Um bloqueio
mais curto pode emitir sinais sem ter amostra de estado true.
`source_state_counts` distingue true/false/unavailable; `source_reason_counts`
explica falhas e `comparison_counts` distingue agree/disagree/unavailable.
Consultas são sequenciais: transição entre duas leituras pode causar divergência,
sem provar qual fonte representa bloqueio. Nenhum boolean é reutilizado após falha.
O JSON resume os sinais recebidos por fonte:
`gnome-lock` para ActiveChanged e `logind-sleep-interface` para PrepareForSleep.
`no-events` significa **não validado**, e `observed` sozinho não prova um par completo.
Conforme [ADR-008](adr/008-ordered-spike-signals.md), `cycles` informa:

- `complete_count`: quantidade de sequências true → false recebidas.
- `pending_start`: true ainda sem false posterior no fim da janela.
- `unpaired_end_count`: quantidade de false recebidos sem true pendente.
- `duplicate_signal_count`: sinais consecutivos iguais; não multiplicam ciclos.

`cycle_status=complete` exige ao menos um ciclo, nenhum início pendente e nenhum
fim sem início. True/true/false conta um ciclo e uma duplicata; false/true tem
contagens iguais, mas nenhum ciclo e status partial. Conexão interrompida produz
failed, mesmo após um par. Fonte ausente produz not-tested; sem sinais, no-events.
Os campos anteriores e o schema JSON v1 são preservados.

Para aceite, compare um ciclo ordenado em ensaio isolado com a ação real e verifique
a continuidade do serviço. Complete descreve apenas os sinais recebidos: não prova
lock efetivo ou confiabilidade de LockedHint. O watcher não persiste intervalos,
histórico do stream ou duração dos ciclos. Falta de ciclo não muda, por si só,
o código de saída de disponibilidade do doctor.
Sem par de suspensão confirmado, um gap continua UNKNOWN.

Cada false de PrepareForSleep com true pendente provoca revalidação das fontes,
resumida em `state_observation.resume_revalidation` por sucesso/falha e motivo.
Durante true pendente, polling de lock é pausado; retomada sem início recebido não
conta como par confirmado. No fim, `post_watch_checks`/`post_watch_status` trazem
leituras novas de X11/GNOME/logind/monitores/alvo gráfico. Disponibilidade final não
esconde falhas intermediárias. Essas consultas não alteram `measurements`, que
continua medindo somente o polling inicial, nem removem a lista estática de pendências.
O doctor retorna 1 se alguma consulta de estado/revalidação ou monitor falhar.

Registre somente disponibilidade, contagens, duração aproximada e limite observado.
Não versione JSON de sessão, journal, screenshots ou conteúdo bruto dos comandos.
O relatório público deve conter apenas evidência técnica sanitizada.

## GNOME e autostart

`gnome-graphical-target` consulta GetUnit e ActiveState do systemd user do host
pelo socket D-Bus montado; não requer systemd de usuário dentro do contêiner.
Isso confirma alvo ativo, não instalação de autostart. No EP-08, ensaiar login/logout
e reboot, ambiente herdado e instância única, com unidade user `PartOf` vinculada ao
alvo, chamando Compose com as variáveis reais de sessão. Se a integração não
iniciar o contêiner, avaliar XDG autostart chamando o mesmo serviço. Não usar
restart always antes do login, habilitar linger nem presumir DISPLAY=:0. Nenhum
serviço/arquivo é instalado na configuração pessoal.

## Correlação Chrome/Chromium — duas janelas/perfis

Esta execução não entrega extensão: o EP-06 implementa o canal de produção.
Antes de fixar o resolver, realizar prova com extensão temporária de diagnóstico
e dois perfis do navegador no host. Não inferir hostname a partir do título.

| Ensaio | Resultado exigido |
| --- | --- |
| Uma janela de browser e uma de terminal | Terminal focado: nenhuma aba recebe duração |
| Duas janelas, perfis diferentes, mesmos títulos | Ambiguidade: aba desconhecida, tempo do browser preservado |
| Foco alternado entre janelas em monitores diferentes | X11 governa foco; primary não dá tempo adicional |
| Mesmo título, IDs API diferentes | IDs da API não equivalem a XIDs |
| Título transitório desativado | Sem candidato inequívoco, aba desconhecida |
| Extensão desconectada ou snapshot >45s | Metadados expiram, app browser continua |
| Janela privada | Sem hostname/título; não inferir domínio |

Registrar apenas candidatos por contagem, estratégia validada e ambiguidade, sem
nomes de perfis, títulos, URLs, PID/XID ou dados corporativos. O caso sintético
`ambiguous-profiles` valida o contrato de fallback; não prova correlação real.

## Fontes técnicas

- [logind no Debian 12](https://manpages.debian.org/bookworm/systemd/org.freedesktop.login1.5.en.html):
  `LockedHint`, GetSession e sinais PrepareForSleep; disponibilidade não garante entrega.
- [interface ScreenSaver do GNOME Shell 43 no Debian](https://sources.debian.org/src/gnome-shell/43.9-0%2Bdeb12u2/data/dbus-interfaces/org.gnome.ScreenSaver.xml/):
  GetActive e ActiveChanged; confiabilidade como lock exige ensaio.
  XML também verificado no recurso instalado `gnome-shell-dbus-interfaces.gresource`.
- [XRandR no Debian 12](https://manpages.debian.org/bookworm/x11-xserver-utils/xrandr.1.en.html):
  consulta de monitores sem comandos de alteração.
- [Chrome Windows API](https://developer.chrome.com/docs/extensions/reference/api/windows):
  IDs de janela no espaço da API do navegador.

## Critério de saída

US-02.1 encerra com diagnóstico e relatório de fontes. US-02.2/03/04 e C0 só encerram
com sinais reais, custo saudável, integração gráfica e prova de perfis. Ausências
têm fallback documentado; fonte crítica não validada impede pressupor coleta confiável.
Não iniciar EP-03 com C0 pendente. Antes da coleta contínua, confirmar almoço real
(padrão provisório 12–13), navegador e quantidade de perfis/monitores, mantendo-os editáveis.
