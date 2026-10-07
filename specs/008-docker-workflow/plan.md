# Plano — Docker/Compose

1. Registrar ADR-007 antes de alterar a arquitetura; atualizar AGENTS e fontes de
   verdade para tornar Docker/Compose obrigatório, preservando métricas e privacidade.
2. Dockerfile com alvos runtime/development e base bookworm, Python configurável
   (3.11 padrão; 3.13 na CI). Instalar ferramentas do spike na imagem e dependências
   dev somente no alvo development. Executar contêiner sem root.
3. compose.yaml com dev isolado e desktop em profile separado; compose.desktop.yaml
   fornece exclusivamente mounts/env de sessão exigidos pelo launcher.
4. Scripts shell mínimos: UID/GID, execução padronizada dos checks e validação dos
   pré-requisitos de sessão. Não rodar Python/linter no host. Não instalar Docker,
   não modificar grupos/credenciais e não recuperar ambiente de outros processos.
5. Adaptar CI, README, handoff, protocolo do spike, backlog e specs afetadas.
   Evidência anterior permanece marcada como histórica, sem reescrever resultados.
6. Validar Compose, imagens, checks offline, build/wheel e doctor dentro do container.
   Testar rejeição de sessão incompleta e documentar a integração gráfica não executada.

Mudança técnica necessária: doctor consulta o manager systemd do host por D-Bus
no contêiner, pois não há systemd de usuário dentro dele. Registrar fallback e
testar respostas/falhas. Demais regras do coletor passivo permanecem iguais.
