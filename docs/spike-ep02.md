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
[ADR-009](adr/009-optional-session-id.md), ausência desse ID deixa somente a leitura
de LockedHint indisponível com missing-graphical-session-id. O launcher não bloqueia
as consultas GNOME/X11 ou PrepareForSleep por esse motivo. Não escolher um ID da
primeira sessão listada, de SSH/TTY ou de outro processo; ID explícito só pode
corresponder à sessão gráfica observada. As demais verificações permanecem obrigatórias.
O [pam_systemd do Debian 12](https://manpages.debian.org/bookworm/libpam-systemd/pam_systemd.8.en.html)
inicializa XDG_SESSION_ID no login. Ausência no terminal indica que essa variável
não chegou ao comando; a causa específica exige diagnóstico e não implica ausência
da sessão no logind. O doctor só usa o ID recebido, sem descoberta automática.
XDG_RUNTIME_DIR é compartilhado entre sessões do mesmo usuário e sozinho não
identifica a sessão gráfica. Não alterar PAM ou exportar ID arbitrário para
transformar o diagnóstico em available.
Sem sessão, `sh scripts/compose run --rm dev digitalmirror doctor` continua
funcionando e identifica fontes ausentes; não é ensaio da sessão real. Nenhum
serviço usa privileged, Docker socket, home completo ou xhost +.
O JSON mostra fontes, motivos/fallbacks e pendências sem título, app, PID, hostname
ou nome de monitor. Mesmo código 0 não encerra os ensaios abaixo.

## Polling, monitores e precisão

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
com consultas durante o ensaio. O JSON resume os sinais recebidos por fonte:
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
