# Instruções de desenvolvimento — DigitalMirror

## Estado e fonte de verdade

EP-01 contém contratos/fixtures e EP-02 tem CLI de diagnóstico; coleta contínua, dados, API e dashboard permanecem pendentes. Leia `docs/product-spec.md`, `docs/system-design.md`, `docs/backlog.md` e `specs/README.md` antes de implementar. As issues #1–#12 correspondem a EP-01–EP-12.

## Escopo técnico

- Alvo: Debian 12 / Python 3.11+ / GNOME / X11. Não use recursos exclusivos do Python 3.12 sem ajustar o suporte explicitamente.
- Monólito modular Python em Docker/Compose, SQLite/WAL, API local e HTML/CSS/JS. Docker é obrigatório conforme ADR-007; não introduzir Electron, broker ou cloud no runtime sem ADR.
- API somente `127.0.0.1:8765`; processo principal único e fila limitada.
- Coletor estritamente passivo: nenhuma simulação de teclado/mouse, mudança de foco, impedimento de idle ou interação com xOne.
- Navegador: foco real no X11 + metadados de extensão. App/aba em segundo plano não recebe foco.

## Execução obrigatória via Docker

- Sempre executar dependências Python, formatter, lint, tipos, testes, build e CLI em contêiner com Docker Compose. Não criar venv nem instalar/executar ferramentas Python no host.
- Build: `sh scripts/compose build dev desktop`. Checks: `sh scripts/compose run --rm dev`. Formatar: `sh scripts/compose run --rm dev ruff format .`.
- Diagnóstico isolado: `sh scripts/compose run --rm dev digitalmirror doctor`. Diagnóstico da sessão real: `sh scripts/compose-desktop run --rm desktop` no terminal GNOME/X11.
- Host fornece Docker Engine/Compose e a sessão gráfica. Sem VM/desktop virtual como substituto de ensaio do host. Imagens usam Debian bookworm/Python 3.11 por padrão.
- Preservar usuário do host: UID/GID iguais em Docker rootful, 0 internos em rootless (mapeiam ao usuário sem privilégios). Usar os launchers para detectar o modo. Sem privileged, xhost +, Docker socket ou home inteiro montado. Acesso gráfico via mounts explícitos read-only de sockets/Xauthority; não criar diretórios no lugar de sockets ausentes.
- Runtime desktop usa rede host Linux para preservar API somente em `127.0.0.1:8765`; nenhum bind `0.0.0.0`. Em rootless, API exige Engine 29.5+ e validação EP-07; versões anteriores atendem checks/doctor por sockets. Dev não recebe sockets e executa checks sem rede.
- Preservar evidências históricas e identificar novas medições em Docker. Ensaios GNOME/X11, autostart/perfis e overhead Docker continuam pendentes até verificação real.
- XDG_SESSION_ID é opcional no diagnóstico desktop (ADR-009). Sem ID, LockedHint fica indisponível; preservar consultas GNOME/X11 e demais verificações do launcher. Não escolher outra sessão nem recuperar ambiente de outros processos.

## Regras que a implementação deve preservar

- Jornada 09–18, almoço configurável de 1h; denominador diário de 480min. Durante o dia usar jornada decorrida com rótulo explícito.
- Separar presença desbloqueada, interação recente, cobertura, tempo sem dados e início/fim declarados.
- Gaps não prolongam o último app e não significam automaticamente computador desligado.
- Reunião/pausa manual não fabrica inputs. Tempo por aba é detalhe do browser, sem dupla contagem.
- UTC para persistência, `America/Sao_Paulo` para calendário e relógio monotônico para durações.
- Títulos persistidos são opt-in; URL completa, teclas, screenshots e conteúdo de páginas não são coletados.
- Nunca commitar bancos, logs de sessão, informações corporativas, tokens ou configurações pessoais.

## Fluxo SDD

1. Escolha um épico/uma fatia, começando por #1 e #2.
2. Crie `specs/<id-nome>/spec.md`, `plan.md` e `tasks.md` com referência aos RF/RNF e critérios da issue.
3. Registre mudanças de semântica/arquitetura em `docs/adr/` antes de alterar o contrato.
4. Implemente uma fatia verificável de ponta a ponta; use fixtures sintéticas para métricas.
5. Execute apenas os testes/checks existentes e relevantes. Documente honestamente o que não pôde testar no ambiente alvo.
6. Atualize spec, checklist e documentação junto com a implementação. Não declare metas de memória/CPU atendidas sem medições.

## Comunicação e validação

Documentação e produto em português brasileiro; identificadores de código podem estar em inglês. Em PRs, descreva o comportamento final, requisitos atendidos, evidência e limitações. O spike deve verificar fontes X11/D-Bus, monitores, suspensão, correlação de perfis de navegador e autostart GNOME antes de fixar pressupostos.
