# Continuar a implementação pela CLI

## Estado inicial

Repositório público criado, Project privado e 12 épicos publicados. Há 48 histórias em checklists. Este commit entrega planejamento, não uma aplicação instalada. A lista de todas as abas/apps abertas e o tempo apenas em segundo plano não foi adicionada ao escopo: o contrato mede foco e interação recente.

## Primeiro trabalho

Leia `AGENTS.md`, `docs/product-spec.md` e `docs/system-design.md`. Comece pela issue #1 (EP-01), detalhando contratos, fixtures e estrutura mínima. Em seguida faça a issue #2 (EP-02) no Debian 12/GNOME/X11 real. Registre disponibilidade e custo das fontes antes de implementar coleta contínua.

## Prompt sugerido para o agente na CLI

> Leia AGENTS.md, docs/product-spec.md, docs/system-design.md, docs/backlog.md e specs/README.md. Trabalhe primeiro no EP-01 (#1) e no spike EP-02 (#2). Crie a spec, o plan e o tasks da fatia antes de implementar. Preserve a observação passiva, a jornada 09–18 com 1h de almoço, foco global de apps/abas, cobertura e lacunas explícitas. Use fixtures sintéticas. Verifique no meu Debian 12/GNOME/X11 janela ativa, idle, bloqueio, monitores, suspensão e integração do autostart. Documente fontes indisponíveis e decisões antes de seguir ao EP-03. Não implemente todos os épicos de uma vez.

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
