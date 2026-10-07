# Continuar a implementação pela CLI

## Estado inicial

Repositório público criado, Project privado e 12 épicos publicados. Há 48 histórias em checklists. Este commit entrega planejamento, não uma aplicação instalada. A lista de todas as abas/apps abertas e o tempo apenas em segundo plano não foi adicionada ao escopo: o contrato mede foco e interação recente.

## Progresso local — 06/10/2026

**Estratégia vigente:** sempre usar Docker/Compose conforme ADR-007 e AGENTS.md.
Build: `sh scripts/compose build dev desktop`; checks: `sh scripts/compose run --rm dev`.
Diagnóstico real: `sh scripts/compose-desktop run --rm desktop` no terminal GNOME/X11.
Não criar venv nem instalar/executar Python ou ferramentas do projeto no host.
As evidências do primeiro spike direto são históricas; novas validações usam Docker.

EP-01 entregue no workspace: spec/plan/tasks, ADRs 001–006, rastreabilidade,
schema e 16 cenários sintéticos, suíte de contratos/CLI e workflow CI.
O motor permanece no EP-05. Issues/Project não foram alterados.

EP-02 tem `digitalmirror doctor`, polling finito e observação passiva de sinais.
Leia [procedimento](spike-ep02.md) e [relatório inicial](spike-ep02-report.md).
Este ambiente Debian 12/Python 3.11 acessa logind, mas não recebeu DISPLAY,
D-Bus de sessão ou identificação da sessão gráfica. Lock/unlock, sleep/resume,
monitores, precisão de foco, dois perfis e autostart real continuam pendentes.
Não iniciar EP-03 nem declarar C0 atingido antes desses ensaios.

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
