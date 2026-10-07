# EP-01 — Contrato do produto e base SDD

Versão do contrato: `1`. Issue: [#1](https://github.com/UnicHeld/digitalmirror/issues/1).
Status: implementado e validado localmente. US-01.1, US-01.2 e US-01.3.
Workflow CI criado; execução remota não solicitada. Motor permanece pendente no EP-05.

## Escopo e requisitos

Formalizar o contrato existente, publicar exemplos sintéticos e verificá-los na CI.
Não implementar coleta contínua, banco, API, dashboard ou motor de métricas neste épico.
RF-01/05/06/07/08/10/11/16 e RNF-07/09/10 orientam os contratos;
os responsáveis pela implementação constam em [rastreabilidade](../../docs/requirements.md).

## Contrato versionado

- Calendário padrão: segunda a sexta, 09–18, `America/Sao_Paulo`, almoço
  provisório 12–13 editável. D=28.800 segundos (480 minutos). Exceções são explícitas.
- Persistência futura em UTC; intervalos `[start,end)`; unidade externa: segundos.
  Duração de coleta usa relógio monotônico. A revisão da política acompanha os resultados.
- E é a jornada decorrida, recortada pelo almoço e por `as_of`; futuro não entra.
  Presença durante o dia deve ser rotulada **jornada decorrida**, separada do progresso diário.
- Estados exclusivos, em prioridade: PAUSED, SUSPENDED confirmado, UNKNOWN,
  LOCKED confirmado, ACTIVE (idle <60s), LOW_ACTIVITY (60≤idle<300s), IDLE (idle≥300s).
  Os limiares são configuráveis. UNKNOWN anterior ao bloqueio significa inconsistência
  de relógio/lacuna; bloqueio confirmado dispensa app/idle para classificar LOCKED.
- P=A+R+I (presença desbloqueada); O=P+L+S (cobertura conhecida).
  E=A+R+I+L+S+U+Q. Presença=100P/E, cobertura=100O/E,
  interação recente=100A/P, progresso diário=100P/D. Divisor zero retorna `null` (N/A).
- App ausente não invalida estado da sessão: `unknown` conserva P. Falta de
  bloqueio/idle necessários torna estado UNKNOWN. Fonte, qualidade (`observed`,
  `estimated`, `unknown`) e motivo acompanham cada intervalo.
- Apps somam P. Abas são detalhamento do browser, sem dupla contagem;
  aba de janela em segundo plano recebe zero. Correlação ambígua recebe aba `unknown`.
- Gaps não prolongam o app e não provam desligamento. Amostras com diferença
  >10s creditam no máximo 5s ao estado anterior; restante UNKNOWN, salvo evento confiável.
  Crash acaba no último checkpoint; perda desejada ≤30s só será validada no EP-04/09.
- Primeiro/último coletado, atividade observada, última interação estimada e
  início/fim declarados são dimensões distintas. Não reconstruir interação antes da coleta.
- Reunião, almoço e declarações são anotações; não criam inputs nem alteram idle.
  Blocos locais de cinco minutos conservam durações; uma amostra não representa todo o bloco.

## Privacidade e limites

Coleta passiva, sem entradas, mudança de foco, screenshots ou interação com xOne.
Títulos persistidos são opt-in; uso transitório para correlação também pode ser desligado.
URL completa, conteúdo de página, teclas e coordenadas de inputs não são coletados.
Modo privado não recebe hostname/título. Diagnósticos não exibem app, PID, XID,
nome de monitor, título, URL, caminhos pessoais, identificadores de sessão ou stderr bruto.
API futura somente `127.0.0.1:8765`, com Host/Origin/sessão/CSRF; nenhum endpoint neste épico.
Fixtures usam apps genéricos e domínios reservados `.example`, sem dados pessoais.
Percentuais não provam produtividade, atraso real, fim do trabalho ou a fórmula do xOne.

## Exemplos e aceite

Given A=360min, R=60min, I=30min e L=30min em um dia normal,
When consolidar, Then P=450min, presença=93,75%, cobertura=100%, interação=80%.

Given consulta às 11h com P=100min, When calcular presença,
Then E=120min, presença=83,33%, progresso diário=20,83% e resultado provisório.

Given crash 14–15h, When retomar, Then U=60min e nenhum app recebe o gap.
Given reunião sem inputs, Then manter IDLE e anotar reunião separadamente.

Critérios: todos os exemplos da seção 4.6 possuem fixture; denominador zero, pausas,
fronteiras de idle, reboot e salto de relógio têm exemplos adicionais; schema rejeita
campos indevidos, intervalos inválidos e valores fora do domínio; cada RF/RNF possui
épico responsável; CI executa os testes existentes por descoberta, incluindo os do
motor quando forem adicionados. Schema validado não equivale a motor implementado.
