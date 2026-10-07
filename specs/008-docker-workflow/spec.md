# Execução padronizada com Docker e Docker Compose

Data: 06/10/2026. Mudança solicitada pelo usuário após EP-01/spike EP-02.
Requisitos: RF-02/03/04/09/15/16; RNF-01/02/03/04/08/09.
Épicos afetados: EP-01/02 e planejamento EP-04/06/07/08/09.
Status: implementado/validado em Docker Python 3.11; limitações em tasks e relatório EP-02.

## Contrato

Docker Engine e Compose v2+ no Linux são pré-requisitos no host. Build,
dependências Python, formatter, lint, tipos, testes, empacotamento e diagnóstico
executam em contêiner. Não criar venv nem instalar ferramentas Python no host.
GNOME/X11 continuam sendo a sessão observada do host; não iniciar desktop virtual.

- `dev`: imagem Debian bookworm/Python 3.11 por padrão, ferramentas de desenvolvimento,
  workspace montado para edição/build, UID/GID do usuário, sem sockets de sessão e
  sem rede durante os checks. Imagem deve ser construída antes da execução offline.
  No Docker rootless, UID/GID 0 internos mapeiam ao usuário não privilegiado do host;
  o launcher adapta esse mapeamento sem conceder root no host.
- `desktop`: imagem de runtime com o CLI atual, sem dependências Python de desenvolvimento,
  filesystem somente leitura e tmpfs; sockets X11, D-Bus de usuário/sistema e
  Xauthority montados explicitamente. Runtime/container roda com UID/GID do host.
  Rootless usa o mesmo mapeamento e exige validar autenticação das fontes da sessão.
  Sem privilégios de host, capabilities extras, Docker socket, home inteiro, /proc do host
  ou credenciais de outras sessões.
- A montagem read-only de um socket limita filesystem, não os métodos de X11/D-Bus.
  A passividade é preservada pelo código; Docker não é isolamento contra a sessão
  à qual foi concedido acesso.
- Rede host apenas no serviço desktop Linux: API futura permanece vinculada a
  `127.0.0.1:8765`, sem publicação de portas nem mudança para `0.0.0.0`.
  Em rootless, acesso direto à rede real exige Engine 29.5+ e validação EP-07;
  doctor por sockets e checks também funcionam com versões anteriores.
- Valores de sessão vêm do terminal GNOME/X11 do usuário, sem hardcode de DISPLAY
  ou caminho de autoridade. O launcher recusa sessão ausente, arquivos/sockets
  inexistentes e Docker remoto para integração gráfica; não cria diretórios substitutos.
  XDG_SESSION_ID é opcional conforme ADR-009: ausência não bloqueia X11/GNOME;
  LockedHint fica indisponível no doctor, sem selecionar outra sessão.
- Histórico de medições diretas é preservado como evidência anterior à migração.
  Novas medições precisam identificar contêiner e incluir overhead Docker separadamente
  no EP-09. Container saudável não prova autostart, foco ou eventos reais.

## Aceite

Given Docker disponível, When executar o comando de checks, Then os testes existentes,
formatter/lint/tipos e build passam dentro do contêiner, com arquivos gerados no UID correto.
Given ambiente sem sessão, When solicitar desktop, Then falhar antes de montar caminhos
vazios/pessoais incorretos. O serviço dev ainda permite diagnosticar fontes ausentes.
Given sessão GNOME/X11, When executar desktop, Then consultar fontes herdadas do host
passivamente; ensaios de transição/perfis/autostart continuam necessários no EP-02.
Given build da imagem, Then .git, venv, dados, logs, tokens e configuração pessoal
não entram no contexto. CI usa o mesmo Compose e não instala Python no runner.

Não implementar banco, API, extensão ou autostart nesta migração. Apenas atualizar
contratos futuros para execução via Compose e manter pendências do spike explícitas.
