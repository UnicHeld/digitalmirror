# DigitalMirror

Observador pessoal e passivo de presença digital para **Debian 12 + GNOME + X11**, com dashboard local.

**Estado:** planejamento e especificação publicados. A aplicação ainda será implementada pela CLI; não há comando de execução disponível nesta versão.

## O que será medido

- Jornada 09h–18h, com uma hora de almoço configurável e 480 minutos previstos.
- Primeira/última atividade observadas e início/fim declarados separadamente.
- Tempo com foco em Cursor, terminal, Spotify e outros aplicativos com janela.
- Tempo por aba e domínio em foco no Chrome/Chromium; Firefox em M2.
- Interação recente, idle, bloqueio, suspensão confirmada e lacunas de coleta.
- Timeline e blocos de cinco minutos; histórico e exportação.

Coleta proposta: a cada 5 segundos. Tempo em foco, interação recente e presença observada são métricas diferentes. Abas/apps somente abertos em segundo plano não recebem tempo em foco. Reprodução de música, comandos de terminal e conteúdo de documentos não fazem parte da coleta.

Tudo funciona localmente, com um processo Python, SQLite, API em loopback e dashboard no navegador. Autostart após login gráfico. Metas de consumo serão verificadas numa sessão de 8h no ambiente alvo.

## Documentação

- [Contrato do produto e métricas](docs/product-spec.md)
- [System design](docs/system-design.md)
- [Backlog: 12 épicos / 48 histórias](docs/backlog.md)
- [Guia para continuar pela CLI](docs/cli-handoff.md)
- [Fluxo de desenvolvimento por especificação](specs/README.md)
- [Instruções para agentes de código](AGENTS.md)

## Planejamento no GitHub

- [Issues públicas](https://github.com/UnicHeld/digitalmirror/issues)
- [Project privado — requer acesso do proprietário](https://github.com/users/UnicHeld/projects/2)

O Project é privado; o repositório, as issues e estes documentos são públicos. Telemetria real, logs pessoais, bancos SQLite e segredos ficam fora do git.

## Começar pela CLI

```bash
git clone https://github.com/UnicHeld/digitalmirror.git
cd digitalmirror
```

Leia `AGENTS.md` e `docs/cli-handoff.md`. Comece por **EP-01 (#1)** e **EP-02 (#2)**: contratos e spike de viabilidade no Debian real. Não implemente todos os épicos de uma vez.

## Limites das métricas

Os indicadores são estimativas independentes e não reproduzem uma fórmula proprietária do xOne. Leitura/reuniões podem acontecer sem teclado ou mouse; o dashboard não apresenta esse tempo como prova de improdutividade. O observador não gera entradas nem interfere em agentes corporativos.
