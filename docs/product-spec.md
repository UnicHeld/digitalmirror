# DigitalMirror — contrato do produto

Versão 0.2 · 06/10/2026 · Contratos/diagnóstico M0 implementados; aplicação M1 pendente.
Estratégia de execução atualizada pelo [ADR-007](adr/007-docker-compose.md).

System design em [system-design.md](system-design.md); backlog em [backlog.md](backlog.md).

## 1. Objetivo e contrato do produto

Construir um observador pessoal de presença digital para Debian 12, GNOME e X11. Ele inicia automaticamente na sessão gráfica, funciona em segundo plano e fornece um dashboard em `http://127.0.0.1:8765`. O usuário consulta seus próprios horários, estados da sessão, aplicações, abas e domínios em foco, além de blocos de cinco minutos.

O resultado é uma estimativa independente. Não conhecemos a fórmula, os limiares nem a configuração do xOne da empresa. Coleta a cada cinco segundos e blocos de cinco minutos são decisões deste projeto, não afirmações sobre o funcionamento do xOne.

O programa observa a sessão sem gerar entradas, mudar foco ou interferir em outros agentes. Tempo em foco mede exposição da janela selecionada; interação recente mede teclado/mouse em termos agregados; nenhum deles prova produtividade. Uma reunião ou leitura pode acontecer sem interação. Esses sinais serão exibidos separadamente.

### Ambiente e decisões iniciais

| Item | Decisão |
| --- | --- |
| Sistema alvo | Debian 12, Python 3.11+, GNOME, X11 |
| Execução e desenvolvimento | Docker Engine local Linux + Compose; Python/ferramentas na imagem bookworm |
| Fuso | `America/Sao_Paulo`; timestamps persistidos em UTC |
| Jornada | Segunda a sexta, 09:00–18:00 |
| Almoço | Uma hora; 12:00–13:00 como padrão provisório, editável por dia |
| Jornada líquida | 480 minutos em um dia útil normal |
| Coleta | A cada 5 s, complementada por eventos de foco/sessão |
| Consolidação | Blocos locais de 5 min; durações reais em segundos |
| Dashboard | Consulta a cada 30 s enquanto estiver aberto |
| Navegador inicial | Chrome/Chromium; Firefox na versão seguinte |
| Recursos | Um processo principal no contêiner; SQLite persistente; HTML/CSS/JS no browser do host |
| Captura de títulos | Desativada na persistência por padrão; opt-in |
| Navegação persistida | Hostname e identificador efêmero de aba; sem caminho/query da URL |
| Coleta fora da jornada | Desativada por padrão; modo opcional separado |
| Retenção | Intervalos detalhados por 30 dias; agregados por 180 dias |

O serviço fica disponível fora da jornada para consultar histórico, mas a telemetria detalhada para. Ao entrar no período previsto, reinicia a observação. Fins de semana, feriados e dias de ausência podem receber exceções configuradas; não dependemos de um calendário externo.


## 2. Desenvolvimento orientado por especificação

A especificação versionada será o contrato de cada entrega. Um documento descreve comportamento observável e exemplos antes de orientar implementação e testes.

### Organização proposta do repositório

| Caminho | Conteúdo |
| --- | --- |
| `README.md` | Objetivo, instalação e primeiros passos |
| `specs/001-foundation/` | Contratos, configuração, saúde e privacidade |
| `specs/002-session-collector/` | Janela, idle, bloqueio, suspensão e falhas |
| `specs/003-workday-engine/` | Jornada, almoço, fórmulas e exemplos |
| `specs/004-browser-focus/` | Abas, domínios e correlação com X11 |
| `specs/005-local-dashboard/` | Telas, filtros, contratos da API |
| `specs/006-desktop-lifecycle/` | Instalação, autostart e desempenho |
| `specs/007-history-calibration/` | Histórico, exportação e comparação |
| `docs/adr/` | Decisões de arquitetura e alternativas |
| `src/digitalmirror/` | Coletor, motor, armazenamento, API e CLI |
| `extensions/chromium/` | WebExtension e manifesto do Native Messaging |
| `packaging/` | Serviço systemd e instalação por usuário |
| `Dockerfile`, `compose*.yaml`, `scripts/` | Imagens, serviços dev/desktop e launchers de sessão/checks |
| `tests/fixtures/` | Sessões sintéticas reproduzíveis |

Cada pasta de spec contém `spec.md`, `plan.md`, `tasks.md` e, quando necessário, `contracts/`. `spec.md` define histórias, regras, casos negativos e critérios de aceite. `plan.md` liga essas regras aos componentes. `tasks.md` ordena trabalhos pequenos com referência ao requisito e ao teste correspondente.

### Fluxo por funcionalidade

1. Escrever ou atualizar a spec, com IDs de requisitos e exemplos Given/When/Then.
2. Registrar dúvidas resolvidas e decisões com impacto em dados ou métricas em um ADR.
3. Planejar contratos de dados/API, dependências e tarefas da fatia vertical.
4. Criar fixtures e testes do comportamento relevante antes ou junto da implementação.
5. Implementar a funcionalidade completa: sinal → intervalo → persistência → métrica → tela.
6. Verificar os critérios de aceite; mudanças de regra voltam à spec.
7. Registrar no PR requisitos atendidos, evidência e limitações reais.

Não exige um framework específico de SDD. O formato funciona com desenvolvimento manual ou assistido por IA. Não iniciaremos com um grande conjunto de interfaces vazias: a primeira fatia captura um sinal, persiste um intervalo e o mostra no dashboard.

### Pronto para desenvolver

Uma história está pronta quando tem objetivo do usuário, regra mensurável, exemplos, dependências, impacto em privacidade e contrato suficiente para implementá-la.

### Pronto para encerrar

Uma história está concluída quando seus critérios passam, os fluxos afetados funcionam no ambiente alvo, spec e implementação concordam, e há documentação necessária. Mudanças no cálculo incluem fixtures; mudanças na sessão incluem teste real no Debian. Os épicos de desempenho incluem medições, não promessas.


## 3. Requisitos funcionais

| ID | Requisito |
| --- | --- |
| RF-01 | Configurar jornada, dias úteis, almoço, fuso e exceções por data |
| RF-02 | Consultar janela ativa, classe da aplicação, PID quando disponível e título opcional |
| RF-03 | Medir tempo desde última interação sem registrar teclas ou coordenadas |
| RF-04 | Identificar bloqueio e desbloqueio; acompanhar suspensão e retomada quando observáveis |
| RF-05 | Separar tempo observado, pausado, suspenso e sem dados |
| RF-06 | Mostrar primeira e última atividade observadas, com origem e precisão |
| RF-07 | Somar tempo em foco por aplicação e participação no total relevante |
| RF-08 | Somar tempo em foco por aba e hostname via extensão local |
| RF-09 | Associar foco ao monitor e registrar qual monitor é principal |
| RF-10 | Exibir resumo diário, timeline e composição dos blocos de cinco minutos |
| RF-11 | Permitir iniciar/encerrar jornada e marcar almoço, pausa e reunião manualmente |
| RF-12 | Exibir classificação configurável de apps/domínios com estado desconhecido |
| RF-13 | Exportar métricas e intervalos selecionados em CSV/JSON |
| RF-14 | Consultar histórico e comparar estimativas com valores informados pelo usuário |
| RF-15 | Iniciar na sessão gráfica e reiniciar após falha sem duplicar intervalos |
| RF-16 | Pausar coleta, aplicar retenção, excluir dados e diagnosticar fontes indisponíveis |

Títulos podem conter nomes de clientes, documentos e tarefas. O padrão armazena app, hostname e um ID de aba, com rótulo como `github.com · aba 2`. O título pode ser usado transitoriamente em memória para correlacionar janela e extensão, mesmo sem persistência; esse comportamento deve ser explicado nas configurações. Se o usuário desativar também o uso transitório, correlações ambíguas aparecem sem identificação de aba.

Captura de janela com foco é global à sessão X11. Uma janela no monitor secundário recebe tempo quando está com foco. Estar visível no monitor principal é um atributo diferente e não recebe tempo adicional. Não há acesso automático ao conteúdo de todas as janelas/abas visíveis.


## 4. Semântica das métricas

### 4.1 Calendário de cálculo

Para um dia normal, `W = [09:00,12:00) ∪ [13:00,18:00)` e `D = duração(W) = 480 min`. Todos os intervalos são semiabertos: início incluído, fim excluído. Intersectar cada intervalo observado com W evita contar almoço e horas externas.

Se o almoço mudar para 12:30–13:30, W muda, mantendo 480 min. O usuário pode marcar o almoço real; enquanto não fechar o intervalo, o dashboard indica resultado provisório. Para consolidar um dia normal, o sistema pede um intervalo de almoço de uma hora ou uma exceção explícita de calendário. Uma pausa maior não aumenta silenciosamente a tolerância: o excesso é uma pausa adicional e permanece na jornada prevista.

Não movemos automaticamente o início previsto para a primeira interação. Começar às 09:20 não transforma a meta em 09:20–18:20. Horas depois de 18:00, quando a coleta externa está habilitada, aparecem separadas e não compensam automaticamente a presença dentro de W.

Até o instante de consulta t, `E(t) = duração(W ∩ (-∞,t))`. Antes das 09:00 E=0; durante o almoço E fica constante; às 18:00 E=D. Durante o dia, os indicadores usam E e são provisórios. O dashboard também mostra progresso em relação a D, com rótulo distinto.

### 4.2 Estados exclusivos da sessão

Cada segundo elegível pertence a exatamente um estado, com a prioridade abaixo. `idle` é o tempo agregado sem interação consultado no X11.

| Prioridade | Estado | Condição |
| --- | --- | --- |
| 1 | `PAUSED` | Coleta pausada explicitamente pelo usuário |
| 2 | `SUSPENDED` | Intervalo confirmado por eventos de suspensão/retomada |
| 3 | `UNKNOWN` | Fonte crítica indisponível, relógio inconsistente ou lacuna não explicada |
| 4 | `LOCKED` | Bloqueio confirmado; nesse estado não precisamos de app ou idle |
| 5 | `ACTIVE` | Sessão desbloqueada e idle < 60 s |
| 6 | `LOW_ACTIVITY` | Sessão desbloqueada e 60 s ≤ idle < 300 s |
| 7 | `IDLE` | Sessão desbloqueada e idle ≥ 300 s |

Os limiares são configuráveis e não representam regras conhecidas do xOne. Falha em obter app não invalida a sessão: ela pode continuar ACTIVE com `app=unknown`. Falha em detectar bloqueio torna a sessão UNKNOWN; bloqueio confirmado permite LOCKED mesmo quando X11 não responde. Sem confirmação de bloqueio, idle ausente impede a classificação ativa/ociosa.

Lacunas não autorizam concluir que o computador estava desligado. Inicialização tardia do coletor, crash, logout, falta de permissão e desligamento podem produzir a mesma ausência de amostras. Exibir o motivo confirmado ou `sem dados`; não inventar presença nem ausência do colaborador.

### 4.3 Fórmulas e denominadores

Definir, depois de intersectar os intervalos com W até t:

- A = segundos ACTIVE.
- R = segundos LOW_ACTIVITY.
- I = segundos IDLE.
- L = segundos LOCKED.
- S = segundos SUSPENDED confirmados.
- U = segundos UNKNOWN.
- Q = segundos PAUSED.
- P = A + R + I: presença digital observada, isto é, sessão desbloqueada com sinais válidos.
- O = A + R + I + L + S: tempo com estado observado.

Invariante: `E = A + R + I + L + S + U + Q`, com tolerância numérica de até 1 ms por recorte. Almoço e futuro não entram nessa soma.

| Indicador | Fórmula | Interpretação |
| --- | --- | --- |
| Presença digital estimada | `100 × P / E` | Percentual da jornada decorrida com sessão desbloqueada observada |
| Cobertura de observação | `100 × O / E` | Quanto do período tem estado conhecido |
| Interação recente na presença | `100 × A / P` | Fração da presença com idle abaixo do limite inicial |
| Progresso da presença diária | `100 × P / D` | Presença já observada em relação às oito horas do dia |
| Tempo sem interação ≥ 5 min | I | Idle alto; pode incluir leitura, vídeo ou reunião |
| Tempo em foco por app | Soma de intervalos P atribuídos ao app | Inclui leitura sem interação; `app desconhecido` conserva o total |
| Participação por app | `100 × foco_app / P` | Soma por apps, incluindo desconhecido, fecha em 100% |
| Tempo por aba/site | Soma de foco do navegador atribuído a aba/site | Detalhamento do tempo do navegador; não somar novamente ao tempo total |
| Classificação corporativa | Foco em categorias configuradas / P | Métrica opcional; regras e desconhecidos ficam visíveis |

Denominador zero resulta em `N/A`, não 0% nem 100%. Baixa cobertura acompanha qualquer percentual com destaque e motivo; ausência de dados não é apresentada como falta de trabalho. Reunião manual e almoço são anotações; reunião não transforma IDLE em ACTIVE nem cria interação fictícia. A tela pode mostrar tempo em reunião em uma dimensão independente.

### 4.4 Primeiro e último horário

Manter quatro horários distintos:

1. Primeira e última coleta: intervalo de funcionamento do observador.
2. Primeira e última atividade observadas: amostras ACTIVE ou transições com interação recente durante W.
3. Última interação estimada: `timestamp_amostra - idle`, somente quando pertence ao trecho efetivamente observado; sem reconstrução retroativa anterior ao início da coleta.
4. Início/fim declarados: marcações manuais de jornada, preservadas como declarações.

O usuário vê automaticamente primeira atividade e última interação observadas. Durante a jornada, o fim aparece como provisório; a marcação “encerrar jornada” estabelece um fim declarado. O encerramento não desliga o dashboard; interrompe a coleta de trabalho daquele dia até retomada explícita.

`Atraso observado = max(0, primeira_atividade_observada - 09:00)`. É uma diferença de horários estimada, acompanhada da cobertura anterior. `Saída antecipada declarada = max(0, 18:00 - fim_declarado)`. Sem declaração, mostrar somente “última interação observada às ...”; isso não prova que o trabalho terminou naquele horário.

### 4.5 Blocos de cinco minutos e modo amostral

Os blocos são alinhados ao relógio local, por exemplo 09:00–09:05, nunca ao horário de inicialização do programa. Cada bloco contém segundos por estado, apps, abas, classificação e cobertura. O bloco corrente é parcial. Recortes no almoço são explícitos.

Uma visualização opcional “amostra a cada 5 min” mostra somente a observação válida mais próxima da fronteira, com distância máxima de 5 s. Ela não transforma essa amostra em cinco minutos de duração. A comparação ilustra o viés de amostragem; não identifica o método da empresa.

### 4.6 Casos que definem o contrato

| Cenário | Resultado esperado |
| --- | --- |
| Coleta válida 09–18, almoço 12–13, A=360, R=60, I=30, L=30 min | P=450; presença=93,75%; cobertura=100%; interação recente=80% |
| Às 11:00, P=100 de 120 min decorridos | Presença até agora=83,33%; progresso diário=20,83% |
| Coletor iniciou 09:20 e P=460 min até 18h | Cobertura=95,83%; 20 min sem dados; não concluir atraso real |
| VS Code 4m50s e Chrome 10s no mesmo bloco | Registrar 290 s e 10 s; uma captura final não redefine a composição |
| GitHub aberto em segundo plano e terminal com foco por 20 min | Terminal recebe 20 min; GitHub recebe zero nesse trecho |
| Usuário lê uma aba por 10 min sem interação | Aba recebe 10 min em foco; estado avança pelos limiares de idle |
| Almoço 12:30–13:30 em um dia alterado | Excluir exatamente esse intervalo e manter 480 min previstos |
| Reunião manual e tela desbloqueada sem inputs | Mostrar reunião; preservar idle observado |
| Suspensão confirmada 14–15h | S=60 min; nenhum app/aba recebe essa hora |
| Crash 14–15h sem evento de suspensão | U=60 min; não prolongar a última aplicação conhecida |
| Duas abas iguais em dois perfis sem correlação segura | Tempo do navegador preservado; aba/site desconhecido |
| Coleta ligada opcionalmente 18–19h | Uma hora externa em separado; presença normal continua limitada a W |


## 6. Metas de qualidade e validação

As metas abaixo serão medidas no Debian do usuário; não são consumo já verificado.
Executar medições em Docker; separar recursos do processo/bridge e overhead do
daemon/contêiner. Evidência anterior à migração não demonstra cumprimento no Docker.

| ID | Meta de aceite |
| --- | --- |
| RNF-01 | Processo principal RSS ≤ 100 MiB em sessão de 8h, dashboard fechado |
| RNF-02 | Principal + bridge ≤ 130 MiB RSS somado, sem incluir o navegador |
| RNF-03 | CPU média ≤ 1% de um núcleo numa sessão representativa; sem crescimento sustentado |
| RNF-04 | Fontes saudáveis: polling de 5s com p95 de atraso ≤ 1s; erro de foco por transição amostral tipicamente ≤ 5s |
| RNF-05 | Resumo diário p95 < 250 ms com 180 dias de agregados e 30 dias de detalhes no fixture de referência |
| RNF-06 | Banco + WAL ≤ 300 MiB após 30 dias com até 2.000 intervalos/dia no fixture de benchmark |
| RNF-07 | Crash abrupto perde no máximo 30s de confirmação e deixa gap identificado |
| RNF-08 | Coleta diária e histórico continuam sem internet |
| RNF-09 | API/socket não acessíveis pela rede local; origens não autorizadas rejeitadas |
| RNF-10 | Totais reconciliam estados, apps e detalhamento de browser sem dupla contagem |

Se o protótipo com subprocessos exceder CPU/memória, migrar o adaptador para conexão nativa antes da entrega. Filas têm limites e métricas de overflow; backpressure não pode consumir memória indefinidamente. Não impor MemoryMax muito baixo e aceitar crashes como forma de cumprir meta.

### Testes relevantes

- Unitários/property tests do recorte em W, almoço, fronteiras de bloco, limiares, denominador zero e conservação de duração.
- Fixtures de mudança de app, duas abas, navegador sem foco, bloqueio, suspensão, crash, gaps, reboot e salto de relógio.
- Contratos da API e mensagens da extensão com versões, schema, duplicatas e ordem.
- Integração em Debian 12/GNOME/X11: duas telas, título opt-in/off, dois perfis, modo privado e ausência de extensão.
- Fluxo completo: iniciar GNOME → serviço automático → usar app/aba → bloquear/desbloquear → consultar dashboard → reiniciar → histórico preservado.
- Segurança local: bind, Host, Origin, CSRF, cookie e IPC privado; payloads inválidos não derrubam o processo.
- Soak de 8h: RSS, CPU, latência, amostras atrasadas e tamanho SQLite/WAL.


## 9. Referências técnicas verificadas

As referências fundamentam interfaces técnicas; decisões de métricas, budgets e calendário acima são escolhas propostas para este produto.

- [Debian Bookworm: xdotool](https://manpages.debian.org/bookworm/xdotool/xdotool.1.en.html): janela ativa e propriedades EWMH usadas em diagnóstico.
- [Debian Bookworm: systemd.special](https://manpages.debian.org/bookworm/systemd/systemd.special.7.en.html): `graphical-session.target` e ciclo de sessão do usuário.
- [Chrome: Tabs API](https://developer.chrome.com/docs/extensions/reference/api/tabs): abas, permissões e consulta da janela mais recentemente focada.
- [Chrome: Native Messaging](https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging): conexão com processo local e lista de origens permitidas.
- [Chrome: ciclo de vida de service workers](https://developer.chrome.com/docs/extensions/develop/concepts/service-workers/lifecycle): eventos, suspensão e conexões nativas.

O alvo Debian 12/GNOME/X11 ainda precisa do spike local. Consultar manuais públicos não substitui executar os testes nesse computador.
