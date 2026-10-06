# Instruções de desenvolvimento — DigitalMirror

## Estado e fonte de verdade

Este repositório começa somente com planejamento. Não presuma existir aplicação, dependências instaladas ou suíte de testes. Leia `docs/product-spec.md`, `docs/system-design.md`, `docs/backlog.md` e `specs/README.md` antes de implementar. As issues #1–#12 correspondem a EP-01–EP-12.

## Escopo técnico

- Alvo: Debian 12 / Python 3.11+ / GNOME / X11. Não use recursos exclusivos do Python 3.12 sem ajustar o suporte explicitamente.
- Monólito modular Python, SQLite/WAL, API local e HTML/CSS/JS. Não introduzir Electron, containers, broker ou cloud no runtime sem justificar em ADR.
- API somente `127.0.0.1:8765`; processo principal único e fila limitada.
- Coletor estritamente passivo: nenhuma simulação de teclado/mouse, mudança de foco, impedimento de idle ou interação com xOne.
- Navegador: foco real no X11 + metadados de extensão. App/aba em segundo plano não recebe foco.

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
