# Tarefas — Docker/Compose

- [x] ADR-007 e instruções permanentes Docker-first em AGENTS/documentação.
- [x] Dockerfile runtime/development, .dockerignore e Compose seguro por serviço.
- [x] Launchers/checks sem Python no host, UID/GID e validação de sessão explícita.
- [x] Doctor consulta o systemd user do host via D-Bus; testes relevantes.
- [x] Workflow CI usa Compose e checks idênticos aos locais; CI remota passou em Python 3.11/3.13.
- [x] Build das imagens e validação de Compose executados em Python 3.11.
- [x] Formatter/lint/tipos/32 testes/build e CLI validados nos contêineres.
- [x] Relatório registra limitações gráficas e overhead/medições ainda pendentes.

[CI remota](https://github.com/UnicHeld/digitalmirror/actions/runs/37550585612)
validou imagens dev/runtime, 32 testes e build sdist/wheel em Python 3.11/3.13.
Sessão GNOME/X11 completa e futura API em rootless Engine 29.5+ permanecem sem
validação nesta entrega. Os checks não encerram EP-02/C0.
