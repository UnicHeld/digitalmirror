# ADR-008 — Ciclos ordenados de sinais no spike

Status: aceito para o diagnóstico EP-02; não escolhe o adaptador de produção.
Requisitos: US-02.2 / RF-04/05 e RNF-09/10.

Contexto: contagens iguais de true/false não demonstram um ciclo de ida e volta.
Um false anterior a true, duplicatas ou uma conexão interrompida podem produzir
essas contagens sem uma observação completa de bloqueio ou suspensão.

Decisão: preservar os campos existentes do doctor JSON v1 e adicionar, por fonte
do watcher, `cycles` e `cycle_status`. Um ciclo completa somente quando true é
seguido de false no mesmo stream observado. True repetido não inicia outro ciclo;
false sem true pendente conta como fim sem início. Contar também sinais consecutivos
iguais e informar um true ainda pendente no fim da janela. Memória constante,
sem histórico de eventos, identificadores, conteúdo bruto ou durações inferidas.

`cycle_status` será `not-tested`, `no-events`, `failed`, `partial` ou `complete`.
Complete exige ao menos um ciclo, nenhum início pendente e nenhum fim sem início;
duplicatas ficam explícitas sem multiplicar ciclos. Falha da conexão prevalece
sobre pares recebidos anteriormente. O status de disponibilidade e o retorno CLI
mantêm a semântica atual: ausência de ciclo não é falha de leitura por si só.

Consequência: o resumo comprova ordem dos sinais recebidos, não sua correspondência
às ações reais, a continuidade do serviço D-Bus ou a confiabilidade de LockedHint.
Não transforma ActiveChanged em prova de bloqueio, não mede tempo suspenso e não
encerra C0. O usuário continua comparando ações voluntárias com ensaios isolados.
Nenhuma mudança na semântica de presença, gaps ou métricas persistidas.

Alternativa rejeitada: parear por `min(true_count, false_count)`, pois perde a ordem.
