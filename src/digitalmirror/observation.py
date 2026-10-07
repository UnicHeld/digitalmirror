"""Contagens finitas de estados de lock e de revalidação, sem histórico pessoal."""

from collections import Counter
from collections.abc import Mapping

from digitalmirror.doctor import Runner, collect_checks, read_lock_checks, run_readonly


class WatchObservation:
    def __init__(self, env: Mapping[str, str], runner: Runner = run_readonly):
        self.env = env
        self.runner = runner
        self.samples = 0
        self.lock_counts: dict[str, Counter[str]] = {}
        self.lock_reasons: dict[str, Counter[str]] = {}
        self.comparisons: Counter[str] = Counter()
        self.resume_count = 0
        self.resume_status: dict[str, Counter[str]] = {}
        self.resume_reasons: dict[str, Counter[str]] = {}
        self.failed = False

    def sample_locks(self) -> None:
        self.samples += 1
        values: dict[str, bool] = {}
        for check in read_lock_checks(self.env, self.runner):
            active = (check.details or {}).get("active")
            if check.status == "available" and type(active) is bool:
                values[check.source] = active
                state = "true" if active else "false"
            else:
                state = "unavailable"
                self.failed = True
            self.lock_counts.setdefault(check.source, Counter())[state] += 1
            self.lock_reasons.setdefault(check.source, Counter())[check.reason] += 1
        if len(values) != 2:
            comparison = "unavailable"
        else:
            comparison = "agree" if values["gnome-lock"] == values["logind-lock"] else "disagree"
        self.comparisons[comparison] += 1

    def revalidate_resume(self) -> None:
        self.resume_count += 1
        for check in collect_checks(self.env, self.runner):
            self.resume_status.setdefault(check.source, Counter())[check.status] += 1
            self.resume_reasons.setdefault(check.source, Counter())[check.reason] += 1
            if check.status != "available":
                self.failed = True

    def report(self) -> dict[str, object]:
        return {
            "status": "degraded" if self.failed else "available",
            "lock_polling": {
                "interval_seconds": 5,
                "samples": self.samples,
                "source_state_counts": self.lock_counts,
                "source_reason_counts": self.lock_reasons,
                "comparison_counts": self.comparisons,
                "limitation": "consultas sequenciais; coincidência não comprova bloqueio efetivo",
            },
            "resume_revalidation": {
                "confirmed_signal_pairs": self.resume_count,
                "source_status_counts": self.resume_status,
                "source_reason_counts": self.resume_reasons,
                "limitation": "read-ok após par recebido; não comprova intervalos ou duração",
            },
        }
