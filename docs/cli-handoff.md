# Continuar a implementação pela CLI

## Retomada atual — investigação em 07/10/2026

EP-02 continua In Progress, C0 pendente e EP-03 Backlog. Esta retomada sucede
`fa3b7bb` (handoff), com implementação anterior `086e553`, e inclui instrumentação
sanitizada e evidências dos ensaios reais de bloqueio e suspensão/retomada.

**Ponto atual:** ADR-011 implementado e doctor real recebido às 22:28 local de
07/10: onze fontes read-ok, associação por VT e LockedHint=false, com Display
ainda vazio. Próximas validações são transições LockedHint em lock/retomada e
polling desse caminho; depois precisão temporal de foco, perfis e ciclo de login.
Formatter/lint/mypy, 67 testes e build via Compose/Python 3.11 aprovados novamente
antes da publicação. Histórico e detalhes dos ensaios preservados abaixo.

`logind-lock.details` agora inclui `candidate_source` mesmo na falha e, após parse
tipado completo, seis booleans `identity_*` e `session_display_status`.
`process_uid_is_root`/`host_uid_matches_process_uid` mostram a relação entre UID
interno e UID real sem revelar valores. Motivo agregado, critérios e seleção do
ADR-010 foram preservados. O campo `resolved_from_user_display` mantém sua
semântica anterior de sucesso. Protocolo de interpretação em
[spike-ep02.md](spike-ep02.md#investigar-session-identity-mismatch).

A captura fornecida nesta retomada informa Debian 12/GNOME 43.9 e duas resoluções;
não identifica o atributo divergente nem comprova a identidade da sessão logind.
O ambiente do agente continua sem DISPLAY/XDG_SESSION_TYPE/XDG_SESSION_ID,
Xauthority/runtime dir ou D-Bus de sessão. Docker disponível é rootless.
Não recuperar ambiente de outros processos nem criar sessão gráfica substituta.

Validação local via Compose/Python 3.11: formatter, lint, mypy, 57 testes e build
sdist/wheel aprovados, inclusive após reconstruir dev/desktop. O primeiro check
parou no lint por duas capturas de variáveis dos testes; o segundo no mypy por
inferência de dict após ampliar details para enums. Ambos corrigidos. A primeira
reconstrução foi bloqueada pelo sandbox em metadados de ~/.docker/buildx; repetição
autorizada concluiu ambas as imagens. Doctor dev e runtime sem mounts gráficos
retornaram degraded/código 1 esperado, com candidate_source=not-attempted.
O doctor gráfico instrumentado foi recebido depois desses checks, conforme abaixo;
watchers de lock e suspensão/retomada recebidos e correlacionados aos relatos.
Checks via Compose/Python 3.11 repetidos antes da publicação: formatter, lint,
mypy, 57 testes e build aprovados. Incremento publicado em `9665660`; a
[CI remota](https://github.com/UnicHeld/digitalmirror/actions/runs/37703204277)
passou em Python 3.11/3.13, com imagens dev/desktop, checks e build. Issue #2 e
Project atualizados com evidências e pendências; EP-02 In Progress, EP-03 Backlog.

### Causa identificada e próximo ensaio

Doctor real recebido às 22:32:01 UTC de 07/10 (19:32:01 local), fornecido pelo
usuário via Compose: dez fontes disponíveis; GNOME GetActive=false, um monitor
principal e janela atribuída. logind-lock continua indisponível, mas agora se
conhece a comparação que falhou:

- candidate_source=user-display; candidato obtido pela sessão primária do UID real.
- identity_id_matches/identity_uid_matches/identity_type_x11/identity_class_user/
  identity_remote_false=true.
- identity_display_matches=false e session_display_status=empty.
- process_uid_is_root=true e host_uid_matches_process_uid=false, coerentes com
  o rootless detectado pelo launcher. A comparação com UID do host passou.

Session.Display vazio não fornece evidência de associação ao DISPLAY observado.
Não foi comprovada a causa upstream da propriedade vazia; não atribuir a Docker,
PAM ou GDM. User.Display indica ID/path de uma sessão, sem substituir o nome X11.
Decisão documentada no ADR-010: manter o critério e logind-lock indisponível;
continuar os ensaios finitos pelo fallback GNOME existente. Não alterar login,
chamar SetDisplay/TakeControl, exportar ID ou selecionar outra sessão.

### Watcher de lock recebido e próximos passos

Ensaio real de 120s informado pelo usuário, observed_at=23:01:16 UTC de 07/10
(20:01:16 local; timestamp da amostra inicial). Duração monotônica 120,003736s.
GNOME recebeu exatamente um ciclo true → false, zero duplicatas/fins sem início
e nenhum início pendente. As 24 consultas GetActive foram read-ok: true=7,
false=17. Não converter essas contagens em duração de bloqueio.

No fim, dez fontes permanecem disponíveis, GNOME=false, um monitor principal e
janela atribuída. logind-lock indisponível nas 24 consultas e ao fim, ainda com
Session.Display vazio; comparação unavailable=24 e degraded são esperados.
Sem eventos PrepareForSleep nem revalidação de retomada nesse ensaio.

O usuário confirmou uma ação de bloqueio, espera de cerca de 15s, desbloqueio
e espera pela saída, corrigindo o atalho informado para Windows+L. O relato
corresponde ao único ciclo e às consultas true/false; fallback GNOME aceito para
esse ensaio no host. Não implica LockedHint validado nem medição de duração.

### Suspensão/retomada recebida

O usuário executou watcher separado de 180s (observed_at=23:05:42 UTC de 07/10,
20:05:42 local; amostra inicial) e relatou suspensão manual por aproximadamente
15s, retomada e retorno do comando. Duração monotônica 180,006353s, sem medir a
duração suspensa. Um ciclo PrepareForSleep e um GNOME completos, sem duplicatas
ou bordas pendentes; não inferir causalidade/ordem entre streams pelo resumo.

GetActive read-ok 35/35 (true=2, false=33), logind-lock indisponível 35/35 e
comparison_counts.unavailable=35. Um par confirmado acionou resume_revalidation:
X11 foco disponível com no-focused-window; classe/PID/workspace/geometria
indisponíveis por esse motivo. Idle, XRandR, GNOME, PrepareForSleep e alvo gráfico
read-ok. A leitura vazia de foco não é erro de acesso X11; o código não reutiliza
app anterior. Não afirmar que a tela estava bloqueada nessa consulta, pois o
resumo não contém snapshot de estados nem ordem entre streams.

Ao fim, classe/PID/workspace/geometria recuperaram e dez fontes estavam read-ok,
GNOME=false e um monitor principal com janela atribuída. Apenas logind-lock
indisponível por Session.Display vazio. state_observation conserva degraded,
incluindo indisponibilidades intermediárias; não ocultar a leitura sem foco.
Par de suspensão e revalidação/recuperação observados, conforme relato real.

Etapa 1 concluída no escopo do spike: bloqueio/desbloqueio pelo fallback GNOME,
suspensão/retomada manual com par logind, revalidação e recuperação final.
A indisponibilidade de LockedHint permanece limitação explícita do ADR-010.
Próximo passo: precisão de foco/monitores, perfis com extensão mínima e
login/logout/instância única, conforme protocolo. Nenhum novo watcher de suspensão
é necessário apenas para apagar no-focused-window do relatório.

Todas as ações gráficas são do usuário. Comparação unavailable e degraded/código 1
são esperados; não declarar LockedHint ou concordância validados.
C0 ainda depende das próximas etapas e da decisão final de adaptadores, incluindo
fallback e limitações logind. Não iniciar EP-03 com C0 pendente.

### Complemento da investigação logind no host

Usuário forneceu consultas diretas no host às 20:19–20:23 local de 07/10:
DISPLAY preenchido e tipo x11; apenas uma sessão na listagem manual e User.Display
indicando a mesma. Consulta explícita retornou LockedHint=no, enquanto self falhou
porque o chamador não pertence a sessão conhecida. LockedHint é acessível no host;
o doctor não o consultou nesse candidato por rejeição da associação DISPLAY.
Não confundir rejeição do projeto com impossibilidade técnica de ler a propriedade.
Não incorporar ID explícito/listagem manual como mecanismo de seleção.

Processos do systemd user manager podem ficar fora de uma session scope; é uma
hipótese documentada para self indisponível, ainda não origem comprovada do
terminal. GetSessionByPID pode ter a mesma limitação. Não recuperar ambiente
de outros processos, escolher outra sessão ou mudar o critério sem ADR/spec.
Próximo passo dessa investigação: comprovar associação passiva ao X11 antes de
incorporar leitura/comparação LockedHint; uma leitura isolada desse estado não valida
transições. Session.Display não foi consultado nesses comandos do usuário.

Host xrandr --listmonitors mostrou dois monitores definidos. Doctor consulta
--listactivemonitors e teve um nos ensaios anteriores; comparar o mesmo comando
em momento/configuração iguais antes de concluir falha do contêiner. wlr-randr
ausente não exige nova dependência para o alvo X11. Evidência complementar do
host registrada sanitizada no relatório, sem IDs/nomes ou saída bruta versionada.

### Próximo ensaio preparado — foco e monitores

Comparação --listmonitors e --listactivemonitors no host e via desktop Compose
recebida em 07/10, aproximadamente 20:41 local. As quatro consultas retornaram
dois monitores; um principal. Usuário relata navegador na tela integrada e
terminal em foco na tela externa; saída compatível com layout estendido.
Nenhuma divergência host/contêiner nesse ensaio. A causa da contagem anterior
de um monitor continua desconhecida; não atribuir à opção active ou a Docker.
Procedimento em
[spike-ep02.md](spike-ep02.md#comparar-monitores-no-host-e-no-contêiner).
Polling recebido: relatório das 23:46:43 UTC de 07/10 (20:46:43 local), 12 amostras/
5s. Dez fontes read-ok em 12/12; logind-lock indisponível 12/12 por Display vazio.
Último snapshot com dois monitores, um principal, janela atribuída e GNOME=false.
Janela 55,208928s, latência p95 236,064ms, atraso p95 0,332ms e CPU 1,542% de um
núcleo, acima da referência de 1%. RSS próprio/maior filho 19.104 KiB cada.
Não comprova topologia constante, identidade do app ou precisão das transições;
não atribuir aumento de CPU ao incremento sem comparar cenários equivalentes.

O doctor publicado não registra sequência de apps ou timestamps de mudanças e
não identifica se a janela atribuída estava no monitor principal/secundário.
Extensão local do ADR-005 acrescenta focused_window_on_primary somente com
atribuição e exatamente um principal, sem novas consultas/identificadores.
Ausência de geometria/foco/interseção ou principal ambíguo omite o campo;
não interpretar ausência como false. Duas leituras reais recebidas às 23:56:12
e 23:56:43 UTC (20:56 local): focused_window_on_primary=false e true nos ensaios
secundário/principal respectivamente. Ambas com count=2, primary_count=1 e
focused_window_assigned=true; dez fontes read-ok, GNOME=false e somente logind-lock
indisponível por Display vazio. Correspondem aos cenários solicitados; classe/ID
do app não são expostos, portanto identidade do aplicativo não está comprovada.
Precisão de transições exige instrumentação finita adicional antes do ensaio de foco;
não declarar RNF-04 atendido pela latência de consulta ou por relato de alternância.
Ambiente do agente continua sem sessão gráfica herdada; ensaio real depende
da execução do usuário no terminal GNOME/X11. Extensão local validada via Compose/
Python 3.11: formatter, lint, mypy, 59 testes e build aprovados; imagens dev/desktop
reconstruídas. Sem commit/push ou CI remota deste incremento. Verificação de
atribuição em snapshots concluída para esses cenários. Próxima fatia: ensaio
finito de mudanças de foco, com referência temporal explícita, depois perfis e
login/logout/instância única. Não repetir doctor isolado para medir erro de foco.
Os 31,161%/26,518% de CPU dessas amostras únicas não substituem o polling de
1,542% ou validam RNF de consumo. Código 1/degraded continua esperado por logind.

### Retomada prioritária — Session.Display e terminal virtual

Usuário pediu aprofundamento do valor vazio. Investigação de 07/10 confirmou no
host GDM 43.0-3 e candidato User.Display ativo, x11/user/local, serviço gdm-password,
Display vazio e VT positivo. Não enumerou sessões ou recuperou ambiente de processos.
Fontes do GDM 43/empacotamento Debian e pam_systemd sustentam que NEW_VT registra
sessão via PAM antes de o launcher iniciar Xorg; RegisterDisplay posterior do GDM
não é SetDisplay do logind. Explicação forte, sem trace do login original: não
atribuir a Docker nem tratar automaticamente como configuração quebrada.
Referências e limitações na seção de investigação upstream do relatório.

Próximo passo antes de retomar foco: comparar XFree86_VT da raiz X11 no host e
desktop Compose com VTNr do mesmo candidato User.Display. Nome da propriedade
sem underscore. Agente sem sessão gráfica herdada, leitura X11 real ainda pendente.
Se coincidir, avaliar associação passiva adicional com seat/atividade/identidade e
revalidação, documentando ADR/spec antes de mudar o critério. Nada autoriza usar
VT positivo isolado, escolher outra sessão ou preencher Display via SetDisplay.
Essa etapa foi respondida pelo usuário: em consulta aproximadamente às 21:58
local, VTNr do candidato e XFree86_VT da raiz no host/Compose coincidiram, com
Display vazio e serviço GDM. Sem número/ID pessoal versionado.

Implementação local do ADR-011 (documentado antes do código) permite o mesmo
candidato só com Display vazio, cinco critérios válidos, VT positivo igual,
seat0 canônico e ativo, Seat.ActiveSession correspondente e releituras consistentes
das nove propriedades/VT X11/ActiveSession. Display preenchido errado não usa VT.
diagnostics.session_association_source=x11-vt identifica sucesso com Display ainda
false/empty; falhas preservam GNOME e nunca leem LockedHint/reutilizam candidato.
Checks via Compose/Python 3.11 aprovados: formatter, lint, mypy, 67 testes e build.
Imagens dev/desktop reconstruídas; checks repetidos na nova imagem dev também
aprovados (67 testes/build). Runtime sem mounts gráficos retornou degraded/código
1 esperado, associação not-validated e VT não tentado; não valida fontes reais.
Doctor real dessa implementação recebido: observed_at=01:28:39.879591 UTC de
08/10 (22:28:39 local de 07/10), onze fontes read-ok e status available. logind-lock
session_validated/resolved_from_user_display=true, associação x11-vt, critérios
VT/seat/atividade/releituras true; identity_display_matches=false e categoria empty
preservadas. LockedHint=false e GNOME=false coincidem nessa consulta sequencial.
Dois monitores, principal único e janela atribuída ao secundário. Uma amostra de
224,139ms não mede consumo médio de polling ou confiabilidade de transições.
Próximo passo: watcher de lock 120s e retomada separados para esse novo caminho,
depois polling para custo das seis consultas extras. Ensaios GNOME anteriores
continuam válidos; não validaram LockedHint, então não encerram essas pendências.
CI remota deste incremento deve ser conferida após a publicação. EP-02 permanece
In Progress, C0 pendente e EP-03 Backlog.

## Histórico — parada em 06/10/2026, 23:17 local

Esta seção preserva o handoff anterior; a retomada vigente está acima. A restrição
de não implementar naquele encerramento se referia somente à sessão anterior.

**Começar aqui, sem reiniciar EP-01.** Implementação atual na main: `086e553`
(ADR-010, resolução validada e consultas durante/ao fim do watcher).
[CI dessa implementação](https://github.com/UnicHeld/digitalmirror/actions/runs/37560776472)
passou em Python 3.11/3.13 via Compose; 53 testes passaram localmente.
EP-01 Done; EP-02 In Progress; EP-03 Backlog; C0 pendente.

Último resultado informado pelo usuário: doctor simples executado no terminal
GNOME/X11 às 02:16:59 UTC de 07/10/2026 (23:16:59 local de 06/10). **Dez fontes
disponíveis**, incluindo GNOME GetActive=false e dois monitores; logind-lock
indisponível por **session-identity-mismatch**. session_validated=false.
Isso confirma execução da versão nova e rejeição do candidato, sem validar LockedHint.
Não há watcher/post_watch_checks nessa saída. Apenas uma amostra: os 29,028% de
CPU em 224,802ms não representam polling contínuo. Resumo no relatório; sem JSON bruto.

O motivo atual não identifica qual comparação falhou: Id, UID, Type, Class,
Remote ou Display. resolved_from_user_display=false também não identifica o
caminho tentado quando há erro: SessionResolution retorna esse campo como false
em qualquer falha. Não concluir que o usuário recebeu um XDG_SESSION_ID explícito,
que DISPLAY é a causa, ou que existe uma sessão alheia, sem evidência adicional.

Próximos passos, nesta ordem:

1. Ler AGENTS.md, README, documentos de produto/design, spec/plan/tasks 002,
   ADR-010 e `src/digitalmirror/session.py`; conferir Git e preservar alterações.
2. Instrumentar motivos por comparação e proveniência do candidato em formato
   sanitizado (booleans/enums), sem imprimir ID/UID/DISPLAY/paths nem valores brutos.
   Adicionar regressões relevantes. Consultas e testes sempre dentro de Compose.
3. Analisar resultado no terminal real, conferir UID real versus UID rootless e
   propriedades de identidade. Corrigir somente o que a evidência justificar;
   não afrouxar validação, escolher outra sessão, fixar ID ou recuperar ambiente
   de processos. Mudança de critério exige ADR/spec antes do código.
4. Reconstruir imagens, executar checks e repetir doctor simples. Após associação
   válida (ou decisão explícita de fallback GNOME com evidência), executar watchers
   separados: bloqueio de 120s com ≥15s bloqueado e ≥15s desbloqueado; suspensão
   de 180s com retomada. Conferir source_state_counts/comparison_counts,
   resume_revalidation e post_watch_checks. Usuário executa todas as ações.
5. Fechada a etapa 1, seguir precisão de foco/monitores, prova de dois perfis com
   extensão mínima, protótipo de login/logout/instância única e decisões finais C0.
   CPU curta de 1,137% > meta de 1% permanece registrada; soak de 8h é EP-09.

O usuário encerrou os ensaios desta sessão e pediu somente registro/publicação.
Não executar novos ensaios gráficos ou implementar a instrumentação acima agora.
Na próxima sessão, retomar da investigação de session-identity-mismatch.
Commit/push e atualização de Project foram autorizados nesta sessão; confirmar
Git e estado remoto ao retomar. Não fechar issue #2 ou mover EP-02 para Done ainda.

Prompt para retomar:

> Leia AGENTS.md e a seção de retomada de docs/cli-handoff.md. Continue o EP-02
> a partir do commit 086e553: o doctor real retornou session-identity-mismatch.
> Primeiro instrumente motivos sanitizados por atributo e investigue a associação
> da sessão, preservando UID real/rootless e validação do DISPLAY. Execute testes
> via Docker Compose e prepare os ensaios de lock/retomada antes de avançar às
> etapas de foco, perfis e login/logout. Não iniciar EP-03 com C0 pendente.

## Estado inicial

Na publicação inicial, o repositório público, o Project privado e os 12 épicos continham somente planejamento, com 48 histórias em checklists. A lista de todas as abas/apps abertas e o tempo apenas em segundo plano não foi adicionada ao escopo: o contrato mede foco e interação recente.

## Progresso publicado — 06/10/2026

**Estratégia vigente:** sempre usar Docker/Compose conforme ADR-007 e AGENTS.md.
Build: `sh scripts/compose build dev desktop`; checks: `sh scripts/compose run --rm dev`.
Diagnóstico real: `sh scripts/compose-desktop run --rm desktop` no terminal GNOME/X11.
Não criar venv nem instalar/executar Python ou ferramentas do projeto no host.
As evidências do primeiro spike direto são históricas; novas validações usam Docker.

EP-01 publicado na main: spec/plan/tasks, ADRs 001–006, rastreabilidade,
schema e 16 cenários sintéticos, suíte de contratos/CLI e workflow CI.
O motor permanece no EP-05. Issues #1/#2/#8/#9 atualizadas com entregas,
pendências e a estratégia Docker. Commit de implementação: `0a552a5`.
Push concluído; [CI remota](https://github.com/UnicHeld/digitalmirror/actions/runs/37550585612)
passou em Python 3.11 e 3.13 via Compose (32 testes e build sdist/wheel).
Issue #1 encerrada; Project privado atualizado: EP-01 Done, EP-02 In Progress.
README do Project inclui Docker/Compose obrigatório; EP-03 permanece no Backlog.

EP-02 tem `digitalmirror doctor`, polling finito e observação passiva de sinais.
Leia [procedimento](spike-ep02.md) e [relatório inicial](spike-ep02-report.md).
Este ambiente Debian 12/Python 3.11 acessa logind, mas não recebeu DISPLAY,
D-Bus de sessão ou identificação da sessão gráfica. O terminal do usuário já
confirmou leitura de X11/GNOME e dois monitores via Compose (evidência abaixo).
Watcher GNOME com ciclos durante bloqueio manual já foi observado; correlação
com a quantidade de ações, LockedHint, fontes após retomada, precisão de
foco/monitor, dois perfis e autostart real continuam pendentes. Um par real de
PrepareForSleep foi recebido durante suspensão/retomada manual (evidência abaixo).
Não iniciar EP-03 nem declarar C0 atingido antes desses ensaios.

Continuação publicada do EP-02 no commit `dfe2a24`: ADR-008 e resumo ordenado
de ciclos do watcher, duplicatas/sinais sem par e falha de conexão explícita.
ADR-009 corrige XDG_SESSION_ID ausente: ID opcional, mantendo cookie/sockets e
LockedHint indisponível sem buscar outra sessão. Override aceita ID vazio.
[CI via Compose](https://github.com/UnicHeld/digitalmirror/actions/runs/37553831948)
passou em Python 3.11/3.13: imagens dev/runtime, formatter, lint, mypy, 40 testes
e build sdist/wheel. Issue #2 e README do Project sincronizados; US-02.1 concluída
como diagnóstico/relatório, sem encerrar os ensaios reais das demais histórias.

Logind sem eventos durante 2s confirma somente conexão, com cycle_status=no-events.
Resultado recebido do terminal após a correção: **10 de 11 fontes disponíveis**,
incluindo foco/idle X11, GNOME e XRandR com dois monitores, um principal e janela
atribuída. Somente LockedHint indisponível por missing-graphical-session-id.
Uma amostra com janela de aproximadamente 181ms não mede CPU média de polling;
os 21,95% reportados não comprovam consumo contínuo. Evidência informada pelo
usuário às 00:56:06 UTC de 07/10 (06/10 local), detalhada no relatório.
Polling posterior de 12 amostras/5s informado pelo usuário: dez fontes read-ok
12/12, janela de 55,203s, latência p95 de 205,275ms, atraso p95 de 0,290ms e RSS
próprio de 18,66 MiB. CPU média de um núcleo de 1,137% excede a referência RNF-03
de ≤1%; não declarar meta de CPU atendida nem RNF de 8h validadas.
Watcher de 120s após ação manual Windows+L: GNOME com dois pares true → false,
zero duplicatas/bordas pendentes e cycle_status=complete. Quantidade de ações
manuais ainda precisa corresponder aos ciclos; LockedHint não foi comparado.
PrepareForSleep sem eventos no primeiro watcher; ensaio posterior de 180s com
suspensão/retomada manual recebeu um ciclo completo logind e um GNOME, zero
duplicatas/bordas pendentes. O usuário informou aproximadamente 10s suspenso e
saída JSON do mesmo comando após retorno; duração suspensa não é medida pelo
resumo nem entra nos 180,004s monotônicos. A amostra X11/GetActive antecede o
watcher e não comprova revalidação de todas as fontes após retomada.
Próximos passos: revalidar fontes após retorno, comparar lock com fonte validada
e correlacionar os dois ciclos Windows+L com ações manuais; depois, precisão,
perfis e integração gráfica conforme o protocolo. Na versão ADR-009, falta de ID
mantinha LockedHint indisponível; não escolher um ID arbitrário.
O agente continua sem ambiente gráfico herdado e não executou esses ensaios reais.

Etapa 1 para fechar o spike implementada no ADR-010: sem ID, consultar somente
User.Display do UID real do host; validar identidade/tipo/classe/localidade/DISPLAY
antes de LockedHint. ID explícito também validado, sem fallback para outro candidato.
Compose recebe DIGITALMIRROR_HOST_UID separado do UID interno rootless. Watcher
consulta estados de lock a cada 5s e revalida fontes após pares de retomada e no fim.
Novos campos JSON v1: event_watch.state_observation e post_watch_checks/status.
Falhas intermediárias persistem no diagnóstico. Formatter, lint, mypy, 53 testes
e build passaram via Compose; imagens reconstruídas. Nenhuma nova dependência.
Primeiro ensaio da versão nova recebido: session-identity-mismatch; investigar
conforme a seção de retomada. Depois, doctor simples para validar resolução e watchers separados
de bloqueio (manter bloqueado/desbloqueado por ≥15s) e suspensão/retomada. Conferir
contagens true/false, comparação de fontes, resume_revalidation e post_watch_checks.
Não declarar etapa 1 concluída ou C0 antes de analisar essas evidências gráficas.

## Primeiro trabalho

Leia `AGENTS.md`, `docs/product-spec.md` e `docs/system-design.md`. EP-01 já está
concluído; continue o EP-02 pela seção de retomada acima. Preserve a evidência
histórica e resolva as pendências reais antes de implementar coleta contínua.

## Prompt sugerido para o agente na CLI

> Leia AGENTS.md, docs/cli-handoff.md, docs/product-spec.md, docs/system-design.md,
> docs/backlog.md e specs/README.md. EP-01 está concluído; continue o spike EP-02
> da pendência session-identity-mismatch registrada no handoff. Atualize spec,
> plan, tasks e ADR antes de mudar critérios. Preserve coleta passiva e privacidade,
> valide pelo Docker/Compose com evidências reais e não avance ao EP-03 com C0 pendente.

Execute toda ferramenta Python, checks e diagnóstico dentro das imagens via os
launchers Compose. A sessão real permanece no host; não substituí-la por Xvfb,
desktop em VM ou sessão criada dentro do contêiner. Rootless adapta UID/GID;
Engine anterior a 29.5 ainda não valida a futura API em loopback com rede host.

## Depois do spike

Ordem: coleta (#3), dados (#4), métricas (#5), abas (#6), dashboard (#7). Após isso, autostart (#8) e histórico (#10); valide a sessão de 8h (#9). Firefox (#11) e calibração (#12) são M2.

Antes de iniciar a programação contínua, confirme o horário real do almoço (padrão provisório 12–13), navegador alvo e quantidade de perfis/monitores. As configurações devem ser editáveis, sem valores pessoais fixados no código.

## Checks de encerramento de M1

- Inicializa sozinho após login gráfico; não exige dashboard aberto.
- Cursor/terminal/Spotify recebem apenas seu tempo em foco.
- Abas sem foco não acumulam duração; ausência da extensão conserva tempo do app.
- Jornada e blocos reconciliam estados; cobertura acompanha os percentuais.
- Crash/reboot/suspensão não criam presença fictícia.
- Privacidade, API local e exportação validadas.
- Memória, CPU e atraso de coleta medidos por 8h; resultados comparados às RNF.
