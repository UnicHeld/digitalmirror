"""Lock amostrado, recuperação e revalidação após pares de retomada."""

import contextlib
import io
import json
import subprocess
import sys
import unittest
from unittest.mock import patch

from test_doctor import X11_ENV, healthy_runner

from digitalmirror.cli import main
from digitalmirror.doctor import Check, CommandResult
from digitalmirror.events import watch_events
from digitalmirror.observation import WatchObservation


def lock_check(source, active=None, reason="read-ok"):
    return Check(
        source,
        "available" if active is not None else "unavailable",
        reason,
        "UNKNOWN se fonte não confirmada",
        {"active": active} if active is not None else None,
    )


class LockObservationTests(unittest.TestCase):
    def test_locked_unlocked_disagree_and_unavailable_are_counted_without_history(self):
        samples = [
            [lock_check("gnome-lock", False), lock_check("logind-lock", False)],
            [lock_check("gnome-lock", True), lock_check("logind-lock", True)],
            [lock_check("gnome-lock", False), lock_check("logind-lock", True)],
            [lock_check("gnome-lock", reason="timeout"), lock_check("logind-lock", False)],
        ]
        observer = WatchObservation(X11_ENV, healthy_runner)
        with patch("digitalmirror.observation.read_lock_checks", side_effect=samples):
            for _ in samples:
                observer.sample_locks()
        report = observer.report()
        polling = report["lock_polling"]
        self.assertEqual(polling["samples"], 4)
        self.assertEqual(
            polling["source_state_counts"]["gnome-lock"], {"false": 2, "true": 1, "unavailable": 1}
        )
        self.assertEqual(
            polling["comparison_counts"], {"agree": 2, "disagree": 1, "unavailable": 1}
        )
        self.assertEqual(report["status"], "degraded")
        self.assertNotIn("history", json.dumps(report))
        self.assertNotIn("/synthetic", json.dumps(report))

    def test_failed_resume_then_recovery_remains_degraded(self):
        observer = WatchObservation(X11_ENV, healthy_runner)
        with patch(
            "digitalmirror.observation.collect_checks",
            side_effect=[
                [Check("x11-focus", "unavailable", "timeout", "unknown")],
                [Check("x11-focus", "available", "read-ok", "unknown")],
            ],
        ):
            observer.revalidate_resume()
            observer.revalidate_resume()
        report = observer.report()
        self.assertEqual(report["status"], "degraded")
        self.assertEqual(report["resume_revalidation"]["confirmed_signal_pairs"], 2)
        self.assertEqual(
            report["resume_revalidation"]["source_status_counts"]["x11-focus"],
            {"unavailable": 1, "available": 1},
        )

    def test_locked_hint_invalid_boolean_keeps_gnome_and_comparison_unknown(self):
        def runner(argv):
            if argv[-1] == "LockedHint":
                return CommandResult('{"type":"b","data":0}')
            return healthy_runner(argv)

        observer = WatchObservation(X11_ENV, runner)
        observer.sample_locks()
        polling = observer.report()["lock_polling"]
        self.assertEqual(polling["source_state_counts"]["gnome-lock"], {"false": 1})
        self.assertEqual(polling["source_state_counts"]["logind-lock"], {"unavailable": 1})
        self.assertEqual(polling["comparison_counts"], {"unavailable": 1})


class WatchRevalidationTests(unittest.TestCase):
    def test_only_ordered_resume_pairs_trigger_checks_and_failure_is_preserved(self):
        real_popen = subprocess.Popen
        children = []
        calls = []
        lines = [
            "/org/freedesktop/login1: org.freedesktop.login1.Manager.PrepareForSleep (false,)",
            "/org/freedesktop/login1: org.freedesktop.login1.Manager.PrepareForSleep (true,)",
            "/org/freedesktop/login1: org.freedesktop.login1.Manager.PrepareForSleep (true,)",
            "/org/freedesktop/login1: org.freedesktop.login1.Manager.PrepareForSleep (false,)",
            "/org/freedesktop/login1: org.freedesktop.login1.Manager.PrepareForSleep (false,)",
        ]

        def spawn(argv, **kwargs):
            payload = "\n".join(lines) + "\n"
            child = real_popen(
                [
                    sys.executable,
                    "-u",
                    "-c",
                    f"import sys,time; sys.stdout.write({payload!r}); "
                    "sys.stdout.flush(); time.sleep(10)",
                ],
                **kwargs,
            )
            children.append(child)
            return child

        def runner(argv):
            calls.append(argv)
            if argv[:2] == ["xprop", "-root"]:
                return CommandResult(reason="timeout")
            return healthy_runner(argv)

        with (
            patch("digitalmirror.events.subprocess.Popen", side_effect=spawn),
            patch("digitalmirror.events.shutil.which", return_value="/synthetic/bin"),
        ):
            report = watch_events(1, ["logind-sleep-interface"], env=X11_ENV, runner=runner)
        observation = report["state_observation"]
        self.assertEqual(observation["resume_revalidation"]["confirmed_signal_pairs"], 1)
        self.assertEqual(
            observation["resume_revalidation"]["source_status_counts"]["x11-focus"],
            {"unavailable": 1},
        )
        self.assertEqual(observation["status"], "degraded")
        self.assertEqual(sum(call[:2] == ["xprop", "-root"] for call in calls), 1)
        self.assertTrue(all(child.poll() is not None for child in children))
        self.assertNotIn("SyntheticPrivate", json.dumps(report))

    def test_post_watch_failure_changes_exit_code_without_changing_initial_measurements(self):
        with (
            patch(
                "digitalmirror.cli.diagnose",
                return_value={
                    "schema_version": 1,
                    "status": "available",
                    "checks": [],
                    "measurements": {"samples": 1, "wall_seconds": 0.2},
                },
            ),
            patch(
                "digitalmirror.cli.watch_events",
                return_value={"sources": {}, "state_observation": {"status": "available"}},
            ),
            patch(
                "digitalmirror.cli.collect_checks",
                return_value=[Check("x11-focus", "unavailable", "timeout", "unknown")],
            ),
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            self.assertEqual(main(["doctor", "--watch-seconds", "1"]), 1)
        report = json.loads(output.getvalue())
        self.assertEqual(report["post_watch_status"], "degraded")
        self.assertEqual(report["post_watch_checks"][0]["reason"], "timeout")
        self.assertEqual(report["measurements"], {"samples": 1, "wall_seconds": 0.2})
