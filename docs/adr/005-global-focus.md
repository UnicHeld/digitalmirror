# ADR-005 — Foco global e abas subordinadas

Status: aceito no planejamento v0.1; investigação no EP-02, implementação EP-03/06.
Contexto: visibilidade e aba selecionada não provam foco da sessão.
Decisão: foco real X11 governa crédito; monitor principal é atributo. Browser recebe
tempo de app e abas apenas detalham esse total. Ambiguidade conserva aba desconhecida.
Consequência: IDs de janela da extensão não são tratados como XIDs; dois perfis
precisam de prova real de correlação. Alternativa rejeitada: creditar apps/abas abertos.
