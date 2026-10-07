# Continuar a implementação pela CLI

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
Próximo ensaio: doctor simples para validar resolução e depois watchers separados
de bloqueio (manter bloqueado/desbloqueado por ≥15s) e suspensão/retomada. Conferir
contagens true/false, comparação de fontes, resume_revalidation e post_watch_checks.
Não declarar etapa 1 concluída ou C0 antes de analisar essas evidências gráficas.

## Primeiro trabalho

Leia `AGENTS.md`, `docs/product-spec.md` e `docs/system-design.md`. Comece pela issue #1 (EP-01), detalhando contratos, fixtures e estrutura mínima. Em seguida faça a issue #2 (EP-02) no Debian 12/GNOME/X11 real. Registre disponibilidade e custo das fontes antes de implementar coleta contínua.

## Prompt sugerido para o agente na CLI

> Leia AGENTS.md, docs/product-spec.md, docs/system-design.md, docs/backlog.md e specs/README.md. Trabalhe primeiro no EP-01 (#1) e no spike EP-02 (#2). Crie a spec, o plan e o tasks da fatia antes de implementar. Preserve a observação passiva, a jornada 09–18 com 1h de almoço, foco global de apps/abas, cobertura e lacunas explícitas. Use fixtures sintéticas. Verifique no meu Debian 12/GNOME/X11 janela ativa, idle, bloqueio, monitores, suspensão e integração do autostart. Documente fontes indisponíveis e decisões antes de seguir ao EP-03. Não implemente todos os épicos de uma vez.

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
