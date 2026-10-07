# ADR-010 — Sessão validada e consultas durante o ensaio

Status: aceito para a etapa 1 do spike EP-02.
Requisitos: US-02.2/03, RF-04/05/16 e RNF-09/10.
Complementa ADR-008 e substitui a ausência de descoberta do ADR-009.

## Decisão

O launcher fornece DIGITALMIRROR_HOST_UID a partir de id -u antes do mapeamento
rootless. Não identificar usuário pela identidade interna do contêiner. Com X11
e DISPLAY locais confirmados, preferir XDG_SESSION_ID explícito; na sua ausência,
consultar GetUser(host UID) e somente User.Display, a sessão gráfica primária
indicada pelo logind. Não enumerar sessões nem escolher a primeira disponível.

Antes de LockedHint, validar Id, User/UID, Type=x11, Class=user, Remote=false e
Display igual ao servidor X11 observado (sufixo de screen opcional). Validar tipos
D-Bus e caminhos, sem emitir ID/UID/DISPLAY/paths. Um ID explícito inválido ou de
outra sessão falha sem tentar um segundo candidato. Se User.Display não corresponder
ao DISPLAY, a fonte fica indisponível; não buscar outra sessão. Revalidar identidade
em cada consulta, sem reutilizar última sessão válida após falha.

Usar busctl --json=short, métodos GetUser/GetSession e propriedades específicas.
Sem GetAll, nomes de usuários, ambiente de outros processos, cookies adicionais,
pid:host ou novos mounts. Não ativar serviço nem pedir autorização interativa.
GNOME continua independente quando a associação ao logind não pode ser provada.

O watcher consulta GetActive e LockedHint a cada 5s. Saída aditiva JSON v1:
contagens true/false/indisponível por fonte, motivos normalizados e comparações
agree/disagree/unavailable. Consultas sequenciais não são snapshot atômico:
divergência não decide qual fonte representa bloqueio real. Não persistir valores
com timestamps, história do stream ou duração de bloqueio. Não inventar estado.

Ao receber PrepareForSleep=false após true, repetir todas as consultas do doctor.
Resumir revalidações por fonte, com contagens de sucesso/falha; não interpretar
eventos sem par como retomada confirmada. Revalidar também ao fim do watcher e
emitir post_watch_checks separadamente das medições anteriores ao watcher.
Falhas de consultas ou monitor mantêm diagnóstico degradado mesmo após recuperação.
Limitar contagens e memória pela duração máxima existente de 900s; manter timeouts.

## Limites

O ensaio permanece finito, sem banco/API/autostart ou mudança de foco/inputs.
Não mede os recursos do futuro coletor, duração suspensa ou precisão de foco.
Read-ok, coincidência de booleans e pares de sinais exigem relato manual para
validar a ação real. Ensaios de etapa 1, perfis e login/logout ainda são necessários
antes de C0. Sem fonte crítica confiável, manter UNKNOWN na coleta futura.

Referências: [logind no Debian 12](https://manpages.debian.org/bookworm/systemd/org.freedesktop.login1.5.en.html)
(User.Display e propriedades Session) e [busctl](https://manpages.debian.org/bookworm/systemd/busctl.1.en.html)
(JSON tipado e consultas de múltiplas propriedades).
