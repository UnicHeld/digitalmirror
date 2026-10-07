# ADR-007 — Docker e Compose como fluxo obrigatório

Status: aceito por solicitação explícita do usuário em 06/10/2026.
Substitui a exclusão de containers no ADR-001 e a instalação Python direta dos
planos anteriores. Complementa ADR-002/006; preserva monólito e semântica de métricas.

## Contexto e decisão

Padronizar desenvolvimento, CI, distribuição e execução local por Docker/Compose.
O host mantém Docker Engine/Compose e a sessão Debian/GNOME/X11. Python e as
ferramentas do projeto ficam na imagem, sem venv ou instalação Python no host.
A imagem usa bookworm e Python 3.11 por padrão; CI também verifica Python 3.13.

Serviço dev: workspace para edição/build, UID/GID do host, rede desligada durante
checks e nenhum socket da sessão. Serviço desktop: runtime em filesystem read-only,
tmpfs, mesmo UID/GID do usuário e mounts explícitos de X11/Xauthority/D-Bus.
Em Docker rootless, UID/GID 0 internos correspondem ao usuário não privilegiado
do host; o launcher detecta esse modo para preservar permissões dos bind mounts
e acesso a sockets. Não concede root no host. Autenticação D-Bus/X11 é verificada
no spike, inclusive nesse namespace. Ver [rootless e mapeamento de UID](https://docs.docker.com/engine/security/rootless/).
Não montar Docker socket, home ou /proc do host, nem usar privileged, xhost +,
capabilities extras ou buscar credenciais/ambiente de outras sessões.
Docker remoto/VM de Docker Desktop não valida a sessão local do Debian; integração
gráfica exige Engine local Linux e paths reais acessíveis ao daemon.

Rede host no desktop preserva o bind futuro `127.0.0.1:8765`, sem `ports` nem
bind `0.0.0.0`. Isso remove o isolamento de rede desse serviço; fica restrito ao
desktop local, com validação Host/Origin/sessão/CSRF no futuro EP-07.
Referências: [rede host](https://docs.docker.com/engine/network/drivers/host/) e
[serviços Compose](https://docs.docker.com/reference/compose-file/services/).
Para a futura API em rootless, exigir Engine 29.5+ e teste de acesso pelo host:
versões anteriores isolam a rede host no RootlessKit. O daemon atual 28.2.2
pode executar checks e doctor por sockets, mas não valida esse contrato de API.
Não atualizar/reconfigurar Docker automaticamente. Referência:
[limitação histórica de rede rootless](https://docs.docker.com/engine/security/rootless/troubleshoot/#historical-limitations).

Mount read-only de socket não torna X11/D-Bus uma API de leitura: os comandos
do projeto permanecem estritamente passivos. O diagnóstico consulta o manager
systemd do usuário do host via D-Bus; não espera systemd rodando no contêiner.
Docker não cria acesso à sessão quando variáveis/sockets estão ausentes.

## Consequências para os próximos épicos

- EP-04: SQLite/configuração em diretórios privados persistentes do usuário,
  montados explicitamente; volumes e WAL sobrevivem ao contêiner. Não apagar
  dados por padrão em stop/rebuild/desinstalação; não usar down -v como rotina.
- EP-06: Chrome permanece no host; launcher Native Messaging do host será shell
  encaminhando stdio para bridge dentro do contêiner. IPC privado e validação
  de UID continuam necessários. Resolver de família de processos ainda requer
  spike; não conceder pid:host automaticamente.
- EP-07: monólito no contêiner e dashboard no navegador do host; API só loopback.
- EP-08: GNOME/systemd user inicia/encerra Compose a partir da sessão real,
  sem restart always/linger que colete antes do login. Instância única e mounts
  renovados após novo login/reboot precisam de teste real.
- EP-09: medir processo/bridge e overhead do Docker separadamente, incluindo
  cgroups/RSS/CPU/latência e comportamento de suspensão. Não reutilizar budgets
  medidos fora do Docker como evidência de execução em contêiner.

Containers não alteram prioridade dos estados, gaps, duração, calendário ou
privacidade. Build inicial requer downloads; imagens prontas e runtime/checks
funcionam offline. Sem metas de recursos declaradas antes das medições reais.
Alternativa substituída: venv e ferramentas locais. Não há desktop virtual para
validar foco da sessão real. Autostart/armazenamento/bridge permanecem planejados.
