# ADR-011 — Associação passiva por VT quando Session.Display está vazio

Status: implementado no spike; associação e leitura reais confirmadas, transições de lock ainda pendentes.
Requisitos: US-02.2, RF-04/16, RNF-09. Complementa o critério DISPLAY do ADR-010.

## Evidência e decisão

Em 07/10/2026 o usuário consultou o mesmo candidato User.Display: Display vazio,
serviço GDM, VT positivo. XFree86_VT na raiz X11 coincidiu com VTNr tanto no host
quanto no desktop Compose. Não versionar números/IDs ou saída bruta. A investigação
do GDM 43 explica como a sessão pode ser registrada antes de iniciar o Xorg.

Manter seleção exclusivamente por ID explícito ou User.Display do UID real do
host, sem segundo candidato. Continuar validando tipos, Id/UID/Type=x11/Class=user/
Remote=false. Display local correspondente mantém o caminho existente. Display
não vazio divergente/inválido sempre rejeita; nunca tentar contornar com VT.

Somente se Display for exatamente vazio e os outros cinco critérios passarem,
permitir associação ao mesmo candidato pelos seguintes requisitos conjuntos:

1. VTNr inteiro unsigned positivo, Seat exatamente o seat padrão `seat0` com
   caminho canônico e Active=true. Restrição a seat0 limita o critério a console
   local com VT; não generalizar para multiseat, Xwayland ou sessão remota.
2. XFree86_VT da raiz do DISPLAY já autenticado, formato INTEGER positivo e
   igual a VTNr. Não fixar número nem recuperar ambiente de processos.
3. Seat.ActiveSession corresponde ao ID e ao caminho do candidato original.
   Consultar propriedade somente do seat validado, sem enumerar sessões/seats
   ou usar a sessão ativa como novo candidato.
4. Releitura das seis propriedades originais mais VTNr/Seat/Active sem mudanças,
   nova leitura XFree86_VT igual e nova confirmação Seat.ActiveSession antes de
   liberar o caminho para LockedHint. Repetir toda associação a cada consulta.

Qualquer falha, tipo inválido ou divergência impede LockedHint; GNOME permanece
independente. Não chamar SetDisplay, TakeControl, SetLockedHint ou alterar login.
Não montar /proc, home, Docker socket ou novos sockets nem mudar UID/frequência.

Diagnóstico JSON v1 aditivo: session_association_source=not-validated/session-display/
x11-vt, vt_association_attempted e comparações booleanas identity_vt_positive,
identity_seat_supported, identity_session_active, identity_vt_matches,
identity_seat_session_matches, identity_revalidation_matches, identity_x11_vt_stable.
Comparações só aparecem após leitura/parse da respectiva etapa. Não emitir VT,
seat/ID/path/UID/DISPLAY. identity_display_matches continua false e categoria empty
na associação por VT; session_validated=true não fabrica Display correspondente.

## Limites e validação

Releituras reduzem corridas, mas não formam transação atômica. Propriedades X11
são evidência do servidor autenticado no mesmo modelo de confiança das fontes
existentes; não são prova criptográfica nem autorização contra cliente X11 hostil.
Troca de VT/seat pode tornar a fonte indisponível, inclusive em lock/retomada.
LockedHint é hint informado pelo desktop; disponibilidade não comprova transições.

Testar sucesso pelos dois caminhos de seleção, recusa dos cinco critérios,
DISPLAY preenchido divergente, VT zero/diferente/ausente, seat incompatível,
sessão inativa, ActiveSession diferente, tipos inválidos, timeout e alterações
nas releituras. Falha após sucesso não reutiliza candidato. Testar privacidade
e ausência de métodos de mutação/enumeração. Depois reconstruir e receber doctor
real; ensaiar lock/desbloqueio e retomada com concordância/falhas preservadas.

Doctor real fornecido pelo usuário em 08/10/2026 às 01:28:39 UTC (07/10 às
22:28:39 local): onze fontes read-ok, associação x11-vt validada e LockedHint=false,
coincidente com GetActive=false nessa leitura sequencial. Display permanece vazio.
Uma amostra não valida bloqueio/desbloqueio, retomada ou estabilidade da associação.

Seis comandos de associação por consulta no caminho VT podem aumentar CPU, além
de LockedHint antes não tentado no candidato rejeitado. Medir
polling novamente e preservar os 1,542% anteriores acima da referência de 1%.
Sem aceite RNF ou C0 por testes sintéticos ou pela coincidência manual inicial.

Referências: [logind Debian 12](https://manpages.debian.org/bookworm/systemd/org.freedesktop.login1.5.en.html)
(VTNr, Seat, Active, ActiveSession, LockedHint) e
[Xorg 21.1.7, AddVTAtoms](https://gitlab.freedesktop.org/xorg/xserver/-/blob/xorg-server-21.1.7/hw/xfree86/common/xf86Init.c)
(XFree86_VT na raiz).
