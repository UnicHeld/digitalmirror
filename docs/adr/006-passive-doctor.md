# ADR-006 — Diagnóstico temporário e passivo de M0

Status: aceito para o spike; adaptador contínuo ainda não escolhido.
Contexto: repositório sem runtime e fontes gráficas dependentes da sessão real.
Decisão: CLI Python 3.11 sem dependências de runtime, subprocessos de leitura com
timeout, sem shell e sem captura de título. stdout apresenta apenas disponibilidade,
motivos normalizados, contagens e custo agregado. Ferramentas instaladas não provam fonte.
GNOME GetActive e logind LockedHint são candidatos; confiabilidade depende de ensaio.
Introspecção de PrepareForSleep não equivale a evento observado. Sem DISPLAY/D-Bus,
não adivinhar sessão nem reutilizar credenciais de outros processos.
Consequência: spike não instala autostart, coleta contínua, API, banco ou extensão;
ensaios reais pendentes impedem C0. Custos de falhas não validam budgets de 8h.
Execução e ferramentas de sistema passam à imagem Docker conforme
[ADR-007](007-docker-compose.md); sockets da sessão vêm do host explicitamente.
Alternativas: dependências nativas antes da medição (adiadas); forçar DISPLAY=:0
ou simular inputs (rejeitadas). Não altera os ADRs 001–005 nem a semântica de métricas.
