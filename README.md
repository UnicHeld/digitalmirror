# DigitalMirror

Observador pessoal e passivo de presença digital para **Debian 12 + GNOME + X11**, com dashboard local.

**Estado:** EP-01 implementado: contratos, ADRs, fixtures sintéticas e CI. EP-02 em andamento: CLI `doctor` passiva, diagnóstico de identidade e ensaios reais de bloqueio/suspensão aceitos no escopo do spike com fallback GNOME. Coleta contínua, banco, API e dashboard ainda não foram implementados. Foco/monitores, perfis, login/logout e decisão final de adaptadores permanecem pendentes; C0 ainda não foi atingido.

## O que será medido

- Jornada 09h–18h, com uma hora de almoço configurável e 480 minutos previstos.
- Primeira/última atividade observadas e início/fim declarados separadamente.
- Tempo com foco em Cursor, terminal, Spotify e outros aplicativos com janela.
- Tempo por aba e domínio em foco no Chrome/Chromium; Firefox em M2.
- Interação recente, idle, bloqueio, suspensão confirmada e lacunas de coleta.
- Timeline e blocos de cinco minutos; histórico e exportação.

Coleta proposta: a cada 5 segundos. Tempo em foco, interação recente e presença observada são métricas diferentes. Abas/apps somente abertos em segundo plano não recebem tempo em foco. Reprodução de música, comandos de terminal e conteúdo de documentos não fazem parte da coleta.

Execução local via **Docker e Docker Compose**, com um processo Python, SQLite,
API em loopback e dashboard no navegador do host. O contêiner observa a sessão
GNOME/X11 do Debian por sockets explícitos. Autostart após login gráfico continua
planejado. Metas de consumo e overhead Docker serão medidos numa sessão de 8h.

## Documentação

- [Contrato do produto e métricas](docs/product-spec.md)
- [System design](docs/system-design.md)
- [Backlog: 12 épicos / 48 histórias](docs/backlog.md)
- [Guia para continuar pela CLI](docs/cli-handoff.md)
- [Fluxo de desenvolvimento por especificação](specs/README.md)
- [Instruções para agentes de código](AGENTS.md)
- [Rastreabilidade RF/RNF](docs/requirements.md)
- [Contratos EP-01](specs/001-foundation/spec.md)
- [Spike EP-02: procedimento](docs/spike-ep02.md) e [relatório](docs/spike-ep02-report.md)
- [Decisões de arquitetura](docs/adr/README.md)
- [Docker/Compose: decisão e limites](docs/adr/007-docker-compose.md)

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

## Desenvolvimento e validação com Compose

Pré-requisitos no host: Docker Engine acessível ao usuário e Docker Compose v2+.
Python e as ferramentas do projeto são instalados somente nas imagens bookworm.
Sempre use os launchers: eles ajustam UID/GID, inclusive em Docker rootless, para
não gerar arquivos com outro dono. Não criar venv ou instalar Python no host.

```bash
sh scripts/compose build dev desktop
sh scripts/compose run --rm dev
```

O segundo comando executa formatter em modo check, lint, mypy, testes e build
sdist/wheel sem rede, usando as dependências instaladas na imagem. Artefatos ficam
em `dist/`, ignorado pelo git. Para comandos individuais:

```bash
sh scripts/compose run --rm dev ruff format .
sh scripts/compose run --rm dev python -m unittest discover -s tests -v
sh scripts/compose run --rm dev digitalmirror doctor
```

O diagnóstico em dev mostra fontes de sessão ausentes: esse serviço não recebe
sockets X11/D-Bus. Testes de schema/coerência não implementam o motor do EP-05.
A CI utiliza o mesmo Compose com Python 3.11/3.13.

## Diagnóstico da sessão real

No terminal GNOME/X11 do Debian, com Docker Engine local Linux e as variáveis
originais da sessão (DISPLAY, XAUTHORITY, XDG_RUNTIME_DIR e D-Bus):

```bash
sh scripts/compose-desktop run --rm desktop
sh scripts/compose-desktop run --rm desktop digitalmirror doctor --samples 12 --interval 5
sh scripts/compose-desktop run --rm desktop digitalmirror doctor --watch-seconds 300
```

O watcher resume ciclos true → false, duplicatas e sinais sem par por fonte.
`cycle_status=complete` confirma somente a ordem recebida; ensaios manuais ainda
devem confirmar bloqueio e suspensão reais. Detalhes no protocolo do spike.

O launcher valida os sockets/cookie antes de montar e não adivinha credenciais.
`XDG_SESSION_ID` é opcional: na ausência, o doctor consulta somente User.Display
do UID real do host fornecido pelo launcher. Valida ID, UID, tipo X11, classe user,
sessão local e DISPLAY antes de ler LockedHint; erro mantém a fonte indisponível.
Com Display exatamente vazio, o ADR-011 permite associação por VT da raiz X11,
seat0 ativo e releituras consistentes do mesmo candidato. Não aceita Display
preenchido divergente por esse caminho, nem altera o metadado no logind.
Não exporte um ID arbitrário. O watcher consulta estados de bloqueio a cada 5s,
resume coincidências/divergências e revalida fontes após pares de retomada e no
fim (`post_watch_checks`). Essas leituras ficam fora das medições iniciais de CPU.
Ensaios manuais continuam necessários; detalhes no ADR-010 e no protocolo.
O serviço desktop usa imagem somente leitura, tmpfs e capabilities removidas.
Em rootless, UID 0 interno corresponde ao usuário sem privilégios do host.
Não configura autostart, bloqueia/suspende o computador nem altera foco. Saída JSON
sanitizada; código 1 indica diagnóstico degradado e 2, argumento/ambiente inválido.

GNOME, browser e monitores observados permanecem no host; Docker não fornece uma
sessão gráfica quando ela está ausente. Ensaios e limitações de rootless/rede em
[protocolo do spike](docs/spike-ep02.md). A API ainda não existe: rede host mantém
o contrato futuro de loopback; Docker rootless exige Engine 29.5+ para esse acesso
direto, a validar no EP-07. Não alterar o daemon automaticamente.

## Limites das métricas

Os indicadores são estimativas independentes e não reproduzem uma fórmula proprietária do xOne. Leitura/reuniões podem acontecer sem teclado ou mouse; o dashboard não apresenta esse tempo como prova de improdutividade. O observador não gera entradas nem interfere em agentes corporativos.
