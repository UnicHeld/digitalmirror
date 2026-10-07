# Fluxo de specs por funcionalidade

Os contratos iniciais estão em `../docs/product-spec.md` e `../docs/system-design.md`.
`001-foundation/` contém o EP-01 implementado; `002-session-collector/` contém a
fatia do spike EP-02, com ensaios reais ainda pendentes. Demais pastas serão criadas
antes da respectiva implementação; uma spec sozinha não significa funcionalidade pronta.

| Pasta | Responsabilidade | Épicos |
| --- | --- | --- |
| `001-foundation/` | Configuração, qualidade, estados, privacidade e contratos | EP-01 / EP-04 |
| `002-session-collector/` | Spike, janela/app, idle, lock/sleep, monitores e gaps | EP-02 / EP-03 |
| `003-workday-engine/` | Jornada, almoço, fórmulas, horários, blocos e regras | EP-05 |
| `004-browser-focus/` | Extensão, IPC, correlação de foco, perfis e privacidade | EP-06 / EP-11 |
| `005-local-dashboard/` | API, telas, filtros, controles e acesso local | EP-07 |
| `006-desktop-lifecycle/` | Instalação, autostart, desempenho e E2E | EP-08 / EP-09 |
| `007-history-calibration/` | Histórico, exportação, retenção e calibração | EP-10 / EP-12 |
| `008-docker-workflow/` | Execução obrigatória Docker/Compose e migração de checks/CI | EP-01/02; planos EP-04/06/07/08/09 |

Todas as specs usam o fluxo Docker/Compose do ADR-007. Não instalar ferramentas
Python no host; checks usam `sh scripts/compose run --rm dev` e sinais reais usam
o launcher desktop com a sessão GNOME/X11 do host explicitamente herdada.

## Arquivos por pasta

- `spec.md`: objetivo, histórias, requisitos RF/RNF, semântica, exemplos Given/When/Then e critérios de aceite.
- `plan.md`: componentes, interfaces, modelo de dados, decisões/ADRs, riscos reais e estratégia de validação.
- `tasks.md`: checklist ordenado com referência ao requisito e ao teste/ensaio que o valida.
- `contracts/`: schemas e exemplos quando interfaces exigirem.

## Exemplo inicial obrigatório

Given jornada 09–18 com almoço 12–13, When A=360min, R=60min, I=30min, L=30min, Then presença desbloqueada P=450min, cobertura=100%, presença estimada=93,75% e interação recente na presença=80%.

Um crash de uma hora deve produzir gap/UNKNOWN, sem estender a última aba. Chrome aberto em segundo plano enquanto o terminal está com foco não recebe tempo em foco. Os demais exemplos da spec também devem virar fixtures de comportamento ao implementar o motor.

## Rastreabilidade

EP → história US → requisito RF/RNF → spec → teste/ensaio → PR. Mudança de regra altera a spec e a versão da política, evitando fórmulas diferentes na API e na interface.
