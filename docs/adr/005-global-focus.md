# ADR-005 — Foco global e abas subordinadas

Status: aceito no planejamento v0.1; investigação no EP-02, implementação EP-03/06.
Contexto: visibilidade e aba selecionada não provam foco da sessão.
Decisão: foco real X11 governa crédito; monitor principal é atributo. Browser recebe
tempo de app e abas apenas detalham esse total. Ambiguidade conserva aba desconhecida.
Consequência: IDs de janela da extensão não são tratados como XIDs; dois perfis
precisam de prova real de correlação. Alternativa rejeitada: creditar apps/abas abertos.

## Diagnóstico de atribuição no EP-02 — 07/10/2026

No spike, acrescentar `focused_window_on_primary` aos detalhes XRandR somente
quando houver geometria válida, interseção com monitor e exatamente um principal.
`true` identifica atribuição ao principal; `false`, a outro monitor. Omitir em
caso de ausência de foco/geometria, janela fora das telas ou principal ausente/
ambíguo. Ausência não equivale a false. Usar a maior área de interseção e o
desempate pela ordem XRandR já implementados; sem novas consultas ou identificadores.

É extensão aditiva do diagnóstico JSON v1, sem alterar crédito de foco ou métricas.
Leituras são sequenciais e não demonstram foco imutável durante a consulta.
Dois ensaios estáveis com relato manual podem verificar a atribuição nas duas
telas; não medem erro de transições nem comprovam tempo por aplicativo/aba.
