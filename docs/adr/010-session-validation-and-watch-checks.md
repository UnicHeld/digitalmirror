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

### Instrumentação da rejeição — 07/10/2026

Preservar `reason=session-identity-mismatch` e os critérios acima. Acrescentar
em `logind-lock.details` a proveniência `candidate_source` (`not-attempted`,
`explicit-session-id` ou `user-display`), inclusive em falhas após a tentativa.
O campo existente `resolved_from_user_display` continua confirmando apenas
resolução bem-sucedida; não deve ser usado para inferir o caminho de uma falha.

Somente após parse completo e tipado das seis propriedades, emitir booleans
`identity_id_matches`, `identity_uid_matches`, `identity_type_x11`,
`identity_class_user`, `identity_remote_false` e `identity_display_matches`.
O enum `session_display_status` distingue `empty`, `nonlocal-or-invalid` e `local`;
não emitir o DISPLAY recebido. Ausência desses campos significa que as comparações
não foram concluídas, nunca que passaram. Expor `process_uid_is_root` e
`host_uid_matches_process_uid` após validar o UID fornecido, sem seus valores;
não usar o UID interno para escolher a sessão. Esses booleans não comprovam
sozinhos o modo rootless, identificado pelo launcher.

A extensão aditiva mantém JSON v1, não acrescenta consultas, fallback, mounts ou
recuperação de ambiente. Divergências múltiplas ficam visíveis sem eleger outra
sessão nem alterar critérios para tornar a fonte disponível.

### Continuação com GNOME — evidência de 07/10/2026

O doctor real das 22:32:01 UTC resolveu candidato por User.Display e confirmou
Id/UID/Type/Class/Remote. Session.Display veio vazio, único atributo que não
atendeu ao critério. User.Display é um par ID/path da sessão gráfica primária;
Session.Display é o nome do servidor X11. Um não substitui o outro.
O manual do Debian 12 documenta SetDisplay como chamada do controlador da sessão
e LockedHint como hint informado pelo desktop. A evidência não determina por
que o controlador/login deixou Display vazio; não atribuir a Docker, PAM ou GDM.

Decisão para o spike finito: manter o critério e logind-lock indisponível. Não
aceitar string vazia como igualdade, chamar SetDisplay/TakeControl, alterar login,
exportar ID ou selecionar outra sessão. Prosseguir com ensaios de GetActive e
ActiveChanged pelo socket GNOME já recebido, e PrepareForSleep pelo barramento
de sistema. É aplicação do fallback independente existente, sem mudança de código
ou de semântica de estados do futuro coletor.

GNOME read-ok=false nesta amostra confirma somente uma leitura. Exigir relato
de um bloqueio manual e um ciclo ordenado correspondente, consultas true/false
com ≥15s em cada estado, conexão sem falha e leitura final coerente. A suspensão
terá ensaio separado, par PrepareForSleep e revalidação das fontes na retomada/fim.
Com logind-lock indisponível, comparison_counts=unavailable e status degraded
são esperados; não declarar concordância de fontes nem LockedHint validado.
Se GNOME não corresponder à ação real ou ficar indisponível, bloqueio permanece
sem fonte validada e a futura classificação deve conservar UNKNOWN.

Essa decisão libera somente os ensaios; não encerra US-02.2 ou C0. A limitação
de associação/comparação logind deve constar da decisão final de adaptadores.

Evidência posterior de 07/10: usuário confirmou Windows+L uma vez; watcher de
120s recebeu um ciclo GNOME e consultas true/false. Suspensão manual em ensaio
de 180s entregou um par logind, acionou revalidação e terminou com dez fontes
read-ok. Na consulta imediata de retomada, foco X11 estava vazio e quatro
propriedades indisponíveis; recuperaram ao fim. Fallback aceito nesse host para
a etapa 1 finita, preservando essa limitação e LockedHint indisponível. Precisão,
perfis, login/logout e decisão final de adaptadores permanecem pendentes em C0.

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
