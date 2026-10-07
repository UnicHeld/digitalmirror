"""Observação finita de sinais; nunca provoca bloqueio ou suspensão."""

from __future__ import annotations

import os
import re
import selectors
import shutil
import subprocess
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from digitalmirror.doctor import Runner, run_readonly
from digitalmirror.observation import WatchObservation

EVENT_PATTERNS = {
    "gnome-lock": re.compile(
        r"^/org/gnome/ScreenSaver: org\.gnome\.ScreenSaver\.ActiveChanged \((true|false),\)$"
    ),
    "logind-sleep-interface": re.compile(
        r"^/org/freedesktop/login1: "
        r"org\.freedesktop\.login1\.Manager\.PrepareForSleep \((true|false),\)$"
    ),
}


def parse_signal(source: str, line: str) -> str | None:
    match = EVENT_PATTERNS[source].search(line)
    return match[1] if match else None


@dataclass
class SignalCycles:
    complete_count: int = 0
    pending_start: bool = False
    unpaired_end_count: int = 0
    duplicate_signal_count: int = 0
    _last_signal: bool | None = None

    def observe(self, active: bool) -> None:
        if self._last_signal is active:
            self.duplicate_signal_count += 1
        self._last_signal = active
        if active:
            self.pending_start = True
        elif self.pending_start:
            self.complete_count += 1
            self.pending_start = False
        else:
            self.unpaired_end_count += 1

    def counts(self) -> dict[str, int | bool]:
        return {
            "complete_count": self.complete_count,
            "pending_start": self.pending_start,
            "unpaired_end_count": self.unpaired_end_count,
            "duplicate_signal_count": self.duplicate_signal_count,
        }

    def status(self, connection_status: str) -> str:
        if connection_status in {"not-tested", "no-events", "failed"}:
            return connection_status
        if self.complete_count and not self.pending_start and not self.unpaired_end_count:
            return "complete"
        return "partial"


def watch_events(
    seconds: int,
    available: Sequence[str],
    env: Mapping[str, str] | None = None,
    *,
    runner: Runner = run_readonly,
) -> dict[str, object]:
    if not 1 <= seconds <= 900:
        raise ValueError("watch-seconds=1..900")
    result: dict[str, dict[str, object]] = {}
    cycles: dict[str, SignalCycles] = {}
    processes: dict[int, tuple[str, subprocess.Popen[bytes]]] = {}
    buffers: dict[int, bytes] = {}
    environment = dict(os.environ if env is None else env, LC_ALL="C")
    observation = WatchObservation(environment, runner)
    sleeping = False
    start = time.monotonic()
    with selectors.DefaultSelector() as selector:
        try:
            for source, bus, dest, path in (
                ("gnome-lock", "--session", "org.gnome.ScreenSaver", "/org/gnome/ScreenSaver"),
                (
                    "logind-sleep-interface",
                    "--system",
                    "org.freedesktop.login1",
                    "/org/freedesktop/login1",
                ),
            ):
                result[source] = {"status": "not-tested", "true_count": 0, "false_count": 0}
                cycles[source] = SignalCycles()
                if source not in available:
                    result[source]["reason"] = "source-unavailable"
                    continue
                if not shutil.which("stdbuf") or not shutil.which("gdbus"):
                    result[source]["reason"] = "missing-command"
                    continue
                try:
                    process = subprocess.Popen(
                        [
                            "stdbuf",
                            "-oL",
                            "gdbus",
                            "monitor",
                            bus,
                            "--dest",
                            dest,
                            "--object-path",
                            path,
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL,
                        env=environment,
                        shell=False,
                    )
                except OSError:
                    result[source]["reason"] = "command-unavailable"
                    continue
                assert process.stdout is not None
                fd = process.stdout.fileno()
                processes[fd] = source, process
                buffers[fd] = b""
                selector.register(fd, selectors.EVENT_READ)
                result[source]["status"] = "watching"
            next_poll = time.monotonic()
            while selector.get_map() and time.monotonic() < start + seconds:
                if not sleeping and time.monotonic() >= next_poll:
                    observation.sample_locks()
                    next_poll = time.monotonic() + 5
                for key, _ in selector.select(
                    min(0.25, max(0, start + seconds - time.monotonic()))
                ):
                    fd = key.fd
                    source, _ = processes[fd]
                    chunk = os.read(fd, 4096)
                    if not chunk:
                        selector.unregister(fd)
                        result[source]["status"] = "failed"
                        result[source]["reason"] = "monitor-ended"
                        continue
                    buffers[fd] += chunk
                    if len(buffers[fd]) > 8192:
                        selector.unregister(fd)
                        result[source]["status"] = "failed"
                        result[source]["reason"] = "output-too-large"
                        continue
                    while b"\n" in buffers[fd]:
                        line, buffers[fd] = buffers[fd].split(b"\n", 1)
                        signal = parse_signal(source, line.decode("utf-8", errors="replace"))
                        if signal:
                            resumed = (
                                source == "logind-sleep-interface"
                                and signal == "false"
                                and cycles[source].pending_start
                            )
                            cycles[source].observe(signal == "true")
                            name = signal + "_count"
                            count = result[source][name]
                            assert isinstance(count, int)
                            result[source][name] = count + 1
                            if source == "logind-sleep-interface":
                                sleeping = signal == "true"
                            if resumed:
                                observation.revalidate_resume()
                                next_poll = time.monotonic()
            for source, process in processes.values():
                if result[source]["status"] == "watching" and process.poll() is not None:
                    result[source]["status"] = "failed"
                    result[source]["reason"] = "monitor-ended"
            for source, item in result.items():
                if item["status"] == "watching":
                    item["status"] = (
                        "observed" if item["true_count"] or item["false_count"] else "no-events"
                    )
                item["cycles"] = cycles[source].counts()
                status = item["status"]
                assert isinstance(status, str)
                item["cycle_status"] = cycles[source].status(status)
        finally:
            for _, process in processes.values():
                if process.poll() is None:
                    process.terminate()
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                if process.stdout is not None:
                    process.stdout.close()
    return {
        "requested_seconds": seconds,
        "elapsed_monotonic_seconds": round(time.monotonic() - start, 6),
        "sources": result,
        "state_observation": observation.report(),
        "limitation": (
            "ciclos dos sinais recebidos; não validam ações reais, continuidade do serviço "
            "ou duração; sem eventos não valida entrega"
        ),
    }
