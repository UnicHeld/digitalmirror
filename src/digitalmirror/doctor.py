"""Spike de fontes: somente leitura, sem persistência de telemetria pessoal."""

from __future__ import annotations

import math
import os
import re
import resource
import selectors
import shutil
import subprocess
import time
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from digitalmirror.session import BUSCTL, SERVICE, SESSION_INTERFACE, json_value, resolve_session

TIMEOUT_SECONDS = 2.0
OUTPUT_LIMIT = 65536


@dataclass(frozen=True)
class CommandResult:
    output: str = ""
    reason: str | None = None


@dataclass(frozen=True)
class Check:
    source: str
    status: str
    reason: str
    fallback: str
    # Apenas contagens/booleans/enums sanitizados, nunca metadados brutos da sessão.
    details: dict[str, bool | int | str] | None = None


Runner = Callable[[list[str]], CommandResult]


def run_readonly(argv: list[str]) -> CommandResult:
    if shutil.which(argv[0]) is None:
        return CommandResult(reason="missing-command")
    env = dict(os.environ, LC_ALL="C")
    try:
        with subprocess.Popen(
            argv, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env, shell=False
        ) as process:
            assert process.stdout is not None
            deadline = time.monotonic() + TIMEOUT_SECONDS
            buffer = bytearray()
            reason = None
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        reason = "timeout"
                        break
                    chunk = os.read(process.stdout.fileno(), 4096)
                    if not chunk:
                        break
                    buffer.extend(chunk)
                    if len(buffer) > OUTPUT_LIMIT:
                        reason = "output-too-large"
                        break
            if reason:
                process.kill()
                process.wait()
                return CommandResult(reason=reason)
            try:
                exit_code = process.wait(timeout=max(0.001, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                return CommandResult(reason="timeout")
            if exit_code != 0:
                return CommandResult(reason="command-failed")
            return CommandResult(output=buffer.decode("utf-8", errors="replace").strip())
    except OSError:
        return CommandResult(reason="command-unavailable")


def parse_active_window(output: str) -> str | None:
    match = re.fullmatch(r"_NET_ACTIVE_WINDOW\(WINDOW\): window id # (0x[0-9a-fA-F]+)", output)
    if not match:
        raise ValueError("invalid-active-window")
    return match[1] if int(match[1], 16) else None


def parse_idle(output: str) -> int:
    if not re.fullmatch(r"[0-9]+", output):
        raise ValueError("invalid-idle")
    return int(output)


def parse_boolean(output: str) -> bool:
    match = re.fullmatch(r"(?:\((true|false),\)|b (true|false))", output)
    if not match:
        raise ValueError("invalid-boolean")
    return (match[1] or match[2]) == "true"


def parse_geometry(output: str) -> tuple[int, int, int, int]:
    fields = dict(re.findall(r"^(X|Y|WIDTH|HEIGHT)=(-?\d+)$", output, re.MULTILINE))
    if set(fields) != {"X", "Y", "WIDTH", "HEIGHT"}:
        raise ValueError("invalid-geometry")
    x, y, width, height = (int(fields[k]) for k in ("X", "Y", "WIDTH", "HEIGHT"))
    if width <= 0 or height <= 0:
        raise ValueError("invalid-geometry")
    return x, y, width, height


def parse_monitors(output: str) -> list[tuple[bool, tuple[int, int, int, int]]]:
    lines = output.splitlines()
    if not lines or not re.fullmatch(r"Monitors: \d+", lines[0]):
        raise ValueError("invalid-monitors")
    count = int(lines[0].split(": ")[1])
    monitors = []
    for line in lines[1:]:
        match = re.fullmatch(
            r"\s*\d+: ([+*]*)(\S+) (\d+)/(\d+)x(\d+)/(\d+)([+-]\d+)([+-]\d+)\s+.*",
            line,
        )
        if not match:
            raise ValueError("invalid-monitors")
        width, height = int(match[3]), int(match[5])
        if width <= 0 or height <= 0:
            raise ValueError("invalid-monitors")
        monitors.append(("*" in match[1], (int(match[7]), int(match[8]), width, height)))
    if len(monitors) != count or count == 0:
        raise ValueError("invalid-monitors")
    return monitors


def monitor_index(
    geometry: tuple[int, int, int, int],
    monitors: list[tuple[bool, tuple[int, int, int, int]]],
) -> int | None:
    x, y, width, height = geometry
    areas = [
        max(0, min(x + width, mx + mw) - max(x, mx)) * max(0, min(y + height, my + mh) - max(y, my))
        for _, (mx, my, mw, mh) in monitors
    ]
    # Ordem XRandR desempata; atribuição transitória, sem persistir nome/coordenadas.
    if not areas or max(areas) == 0:
        return None
    return max(range(len(areas)), key=lambda index: areas[index])


def _read_check(
    runner: Runner,
    source: str,
    argv: list[str],
    parser: Callable[[str], object],
    fallback: str,
) -> Check:
    result = runner(argv)
    if result.reason:
        return Check(source, "unavailable", result.reason, fallback)
    try:
        parser(result.output)
    except ValueError:
        return Check(source, "unavailable", "invalid-response", fallback)
    return Check(source, "available", "read-ok", fallback)


def _property(output: str, pattern: str) -> object:
    match = re.search(pattern, output, re.MULTILINE)
    if not match:
        raise ValueError("invalid-property")
    return match


def _graphical_target_check(runner: Runner) -> Check:
    fallback = "avaliar XDG autostart no EP-08; não habilitar linger"
    base = ["gdbus", "call", "--session", "--dest", "org.freedesktop.systemd1"]
    result = runner(
        base
        + [
            "--object-path",
            "/org/freedesktop/systemd1",
            "--method",
            "org.freedesktop.systemd1.Manager.GetUnit",
            "graphical-session.target",
        ]
    )
    match = (
        re.fullmatch(
            r"\(objectpath '(/org/freedesktop/systemd1/unit/[a-zA-Z0-9_]+)',\)", result.output
        )
        if not result.reason
        else None
    )
    if not match:
        return Check(
            "gnome-graphical-target", "unavailable", result.reason or "invalid-response", fallback
        )
    # Ler o manager do host pelo socket da sessão; não exigir systemd no contêiner.
    result = runner(
        base
        + [
            "--object-path",
            match[1],
            "--method",
            "org.freedesktop.DBus.Properties.Get",
            "org.freedesktop.systemd1.Unit",
            "ActiveState",
        ]
    )
    state = re.fullmatch(r"\(<\s*'([a-z-]+)'\s*>,\)", result.output) if not result.reason else None
    if not state:
        return Check(
            "gnome-graphical-target", "unavailable", result.reason or "invalid-response", fallback
        )
    active = state[1] == "active"
    return Check(
        "gnome-graphical-target",
        "available" if active else "unavailable",
        "read-ok" if active else "target-inactive",
        fallback,
    )


def read_lock_checks(env: Mapping[str, str], runner: Runner = run_readonly) -> list[Check]:
    checks = []
    if env.get("DBUS_SESSION_BUS_ADDRESS"):
        result = runner(
            [
                "gdbus",
                "call",
                "--session",
                "--dest",
                "org.gnome.ScreenSaver",
                "--object-path",
                "/org/gnome/ScreenSaver",
                "--method",
                "org.gnome.ScreenSaver.GetActive",
            ]
        )
        active = None
        reason = result.reason
        if not reason:
            try:
                active = parse_boolean(result.output)
            except ValueError:
                reason = "invalid-response"
        checks.append(
            Check(
                "gnome-lock",
                "unavailable" if reason else "available",
                reason or "read-ok",
                "LockedHint da sessão validada; senão UNKNOWN",
                {"active": active} if active is not None else None,
            )
        )
    else:
        checks.append(
            Check(
                "gnome-lock",
                "unavailable",
                "missing-session-bus",
                "LockedHint da sessão validada; senão UNKNOWN",
            )
        )
    session = resolve_session(env, runner)
    active = None
    reason = session.reason
    if session.path:
        result = runner(
            BUSCTL + ["get-property", SERVICE, session.path, SESSION_INTERFACE, "LockedHint"]
        )
        reason = result.reason
        if not reason:
            try:
                value = json_value(result.output, "b")
                if type(value) is not bool:
                    raise ValueError("invalid-response")
                active = value
            except (ValueError, TypeError):
                reason = "invalid-response"
    details: dict[str, bool | int | str] = {
        "session_validated": session.path is not None,
        "resolved_from_user_display": session.from_user_display,
        **session.diagnostics,
    }
    if active is not None:
        details["active"] = active
    checks.append(
        Check(
            "logind-lock",
            "unavailable" if reason else "available",
            reason or "read-ok",
            "GNOME validado; senão UNKNOWN",
            details,
        )
    )
    return checks


def collect_checks(env: Mapping[str, str], runner: Runner = run_readonly) -> list[Check]:
    checks: list[Check] = []
    x11 = env.get("XDG_SESSION_TYPE") == "x11" and bool(env.get("DISPLAY"))
    session_reason = "missing-display" if not env.get("DISPLAY") else "x11-session-not-confirmed"
    fallback_focus = "app=unknown; não reutilizar foco anterior"
    geometry = None
    if not x11:
        checks.extend(
            Check(name, "unavailable", session_reason, fallback)
            for name, fallback in (
                ("x11-focus", fallback_focus),
                ("window-class", fallback_focus),
                ("window-pid", "PID opcional; app=unknown se classe ausente"),
                ("window-workspace", "workspace desconhecido"),
                ("window-geometry", "monitor desconhecido"),
                ("x11-idle", "UNKNOWN se bloqueio não confirmado"),
                ("xrandr-monitors", "monitor desconhecido; foco global preservado"),
            )
        )
    else:
        active = runner(["xprop", "-root", "_NET_ACTIVE_WINDOW"])
        window = None
        reason = active.reason
        if not reason:
            try:
                window = parse_active_window(active.output)
            except ValueError:
                reason = "invalid-response"
        checks.append(
            Check(
                "x11-focus",
                "unavailable" if reason else "available",
                reason or ("read-ok" if window else "no-focused-window"),
                fallback_focus,
            )
        )
        if window:
            # Nunca solicitar _NET_WM_NAME/WM_NAME ou passar opção de mutação.
            props = runner(["xprop", "-id", window, "WM_CLASS", "_NET_WM_PID", "_NET_WM_DESKTOP"])
            for source, pattern, fallback in (
                ("window-class", r'^WM_CLASS\(STRING\) = ".+", ".+"$', fallback_focus),
                (
                    "window-pid",
                    r"^_NET_WM_PID\(CARDINAL\) = [1-9][0-9]*$",
                    "PID opcional; preferir classe",
                ),
                (
                    "window-workspace",
                    r"^_NET_WM_DESKTOP\(CARDINAL\) = [0-9]+$",
                    "workspace desconhecido",
                ),
            ):
                valid = not props.reason and bool(re.search(pattern, props.output, re.MULTILINE))
                checks.append(
                    Check(
                        source,
                        "available" if valid else "unavailable",
                        "read-ok" if valid else props.reason or "invalid-response",
                        fallback,
                    )
                )
            result = runner(["xdotool", "getwindowgeometry", "--shell", window])
            if not result.reason:
                try:
                    geometry = parse_geometry(result.output)
                except ValueError:
                    result = CommandResult(reason="invalid-response")
            checks.append(
                Check(
                    "window-geometry",
                    "unavailable" if result.reason else "available",
                    result.reason or "read-ok",
                    "monitor desconhecido",
                )
            )
        else:
            checks.extend(
                Check(name, "unavailable", reason or "no-focused-window", fallback_focus)
                for name in ("window-class", "window-pid", "window-workspace", "window-geometry")
            )
        checks.append(
            _read_check(
                runner, "x11-idle", ["xprintidle"], parse_idle, "UNKNOWN se bloqueio não confirmado"
            )
        )
        result = runner(["xrandr", "--listactivemonitors"])
        details: dict[str, bool | int | str] | None = None
        if not result.reason:
            try:
                monitors = parse_monitors(result.output)
                index = monitor_index(geometry, monitors) if geometry else None
                details = {
                    "count": len(monitors),
                    "primary_count": sum(m[0] for m in monitors),
                    "focused_window_assigned": index is not None,
                }
                if index is not None and details["primary_count"] == 1:
                    details["focused_window_on_primary"] = monitors[index][0]
            except ValueError:
                result = CommandResult(reason="invalid-response")
        checks.append(
            Check(
                "xrandr-monitors",
                "unavailable" if result.reason else "available",
                result.reason or "read-ok",
                "monitor desconhecido",
                details,
            )
        )

    session_bus = bool(env.get("DBUS_SESSION_BUS_ADDRESS"))
    checks.extend(read_lock_checks(env, runner))
    checks.append(
        _read_check(
            runner,
            "logind-sleep-interface",
            [
                "gdbus",
                "introspect",
                "--system",
                "--dest",
                "org.freedesktop.login1",
                "--object-path",
                "/org/freedesktop/login1",
            ],
            lambda output: _property(output, r"\bPrepareForSleep\s*\(\s*b\s+\w+\s*\)"),
            "sem evento confirmado, lacuna é UNKNOWN",
        )
    )
    if session_bus and env.get("XDG_RUNTIME_DIR"):
        checks.append(_graphical_target_check(runner))
    else:
        checks.append(
            Check(
                "gnome-graphical-target",
                "unavailable",
                "missing-user-session",
                "validar na sessão GNOME real",
            )
        )
    return checks


def percentile95(values: list[float]) -> float:
    return sorted(values)[math.ceil(len(values) * 0.95) - 1]


def diagnose(
    samples: int = 1,
    interval: float = 5.0,
    *,
    env: Mapping[str, str] | None = None,
    runner: Runner = run_readonly,
) -> dict[str, object]:
    if not 1 <= samples <= 720 or not math.isfinite(interval) or not 5 <= interval <= 60:
        raise ValueError("samples=1..720; interval=5..60 segundos finitos")
    start = time.monotonic()
    cpu_start = time.process_time()
    child_start = resource.getrusage(resource.RUSAGE_CHILDREN)
    latencies, delays = [], []
    counts: dict[str, Counter[str]] = {}
    reason_counts: dict[str, Counter[str]] = {}
    checks: list[Check] = []
    for index in range(samples):
        deadline = start + index * interval
        time.sleep(max(0.0, deadline - time.monotonic()))
        sample_start = time.monotonic()
        delays.append(max(0.0, sample_start - deadline))
        checks = collect_checks(os.environ if env is None else env, runner)
        latencies.append(time.monotonic() - sample_start)
        for check in checks:
            counts.setdefault(check.source, Counter())[check.status] += 1
            reason_counts.setdefault(check.source, Counter())[check.reason] += 1
    wall = time.monotonic() - start
    child_end = resource.getrusage(resource.RUSAGE_CHILDREN)
    own_cpu = time.process_time() - cpu_start
    child_cpu = (
        child_end.ru_utime + child_end.ru_stime - child_start.ru_utime - child_start.ru_stime
    )
    healthy = all(count["unavailable"] == 0 for count in counts.values())
    return {
        "schema_version": 1,
        "observed_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "scope": "spike-only; sem coleta contínua, banco, API ou autostart instalado",
        "status": "available" if healthy else "degraded",
        "checks": [asdict(check) for check in checks],
        "source_status_counts": counts,
        "source_reason_counts": reason_counts,
        "measurements": {
            "samples": samples,
            "interval_seconds": interval,
            "wall_seconds": round(wall, 6),
            "poll_latency_p95_seconds": round(percentile95(latencies), 6),
            "schedule_delay_p95_seconds": round(percentile95(delays), 6),
            "own_cpu_seconds": round(own_cpu, 6),
            "children_cpu_seconds": round(child_cpu, 6),
            "cpu_pct_one_core": round(100 * (own_cpu + child_cpu) / wall, 3) if wall else None,
            # Linux: ru_maxrss em KiB; filhos é o maior filho, não RSS somado.
            "own_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "largest_child_peak_rss_kib": child_end.ru_maxrss,
        },
        "pending_validation": [
            "bloqueio/desbloqueio reais e confiabilidade de GetActive/LockedHint",
            "suspensão/retomada com par PrepareForSleep observado",
            "precisão de transições de foco e polling saudável",
            "dois perfis/janelas com metadados de extensão e correlação inequívoca",
            "autostart pós-login, ambiente gráfico, logout e instância única",
            "metas RNF de 8h: não verificadas pelo spike",
        ],
    }
