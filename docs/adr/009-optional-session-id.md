# ADR-009 — ID de sessão opcional no diagnóstico desktop

Status: aceito para corrigir o launcher do spike EP-02.
Requisitos: US-02.1/03, RF-04/15/16 e RNF-09.

Contexto: o usuário executou o launcher no terminal GNOME/X11 e recebeu
`XDG_SESSION_ID da sessão não foi recebido.`. A variável ausente não impede
acesso aos sockets X11/D-Bus nem consultas GNOME GetActive/ActiveChanged ou
PrepareForSleep. O ID é usado somente para selecionar LockedHint no diagnóstico.

Decisão: remover a exigência de XDG_SESSION_ID no preflight e permitir valor vazio
no override Compose. Preservar todas as demais verificações de sessão, DISPLAY,
Xauthority, sockets e Docker local. O doctor já trata ID ausente/inválido como
`logind-lock=unavailable`, motivo `missing-graphical-session-id`, sem consultar
outra sessão. A saída permanece degradada quando essa fonte não está disponível.

Não resolver automaticamente um ID com a primeira sessão listada, uma sessão
SSH/TTY, o processo de um servidor de terminal ou um valor fixo. Não ler ambiente
ou cookies de outros processos. Fontes GNOME/X11 independentes continuam sendo
consultadas; confiabilidade de bloqueio ainda exige ensaio real.

Consequências: o launcher deixa de bloquear o spike por uma fonte auxiliar ausente.
LockedHint permanece sem validação até receber um ID explícito válido. Isso não
declara C0 atingido, não muda estados/métricas e não instala autostart.

Referência: [contrato logind no Debian 12](https://manpages.debian.org/bookworm/systemd/org.freedesktop.login1.5.en.html).
