"""CLI de M0. Nenhum comando inicia coleta ou modifica a sessão."""

import argparse
import json
import os
from dataclasses import asdict

from digitalmirror.doctor import collect_checks, diagnose
from digitalmirror.events import watch_events


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DigitalMirror — diagnóstico passivo M0")
    commands = parser.add_subparsers(dest="command", required=True)
    doctor = commands.add_parser("doctor", help="Diagnosticar fontes sem alterar a sessão")
    doctor.add_argument("--samples", type=int, default=1, help="Amostras finitas (1–720)")
    doctor.add_argument("--interval", type=float, default=5.0, help="Intervalo em segundos (5–60)")
    doctor.add_argument(
        "--watch-seconds",
        type=int,
        default=0,
        help="Observar sinais passivamente por 0–900 segundos",
    )
    args = parser.parse_args(argv)
    if not 0 <= args.watch_seconds <= 900:
        parser.error("watch-seconds=0..900")
    try:
        report = diagnose(args.samples, args.interval)
    except ValueError as error:
        parser.error(str(error))
    if args.watch_seconds:
        # O watcher é posterior ao polling e não integra sua medição de custo.
        checks = report["checks"]
        assert isinstance(checks, list)
        watch = watch_events(
            args.watch_seconds,
            [check["source"] for check in checks if check["status"] == "available"],
        )
        report["event_watch"] = watch
        # Uma leitura final é distinta da medição de polling anterior ao watcher.
        post_checks = collect_checks(os.environ)
        report["post_watch_checks"] = [asdict(check) for check in post_checks]
        report["post_watch_status"] = (
            "available" if all(check.status == "available" for check in post_checks) else "degraded"
        )
        sources = watch["sources"]
        assert isinstance(sources, dict)
        observation = watch["state_observation"]
        assert isinstance(observation, dict)
        if (
            any(source["status"] == "failed" for source in sources.values())
            or observation["status"] != "available"
            or report["post_watch_status"] != "available"
        ):
            report["status"] = "degraded"
    print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
    return 0 if report["status"] == "available" else 1
