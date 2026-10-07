import contextlib
import io
import json
import subprocess
import sys
import unittest
from unittest.mock import patch

from digitalmirror.cli import main
from digitalmirror.events import SignalCycles, watch_events


class SignalCycleTests(unittest.TestCase):
    def test_same_totals_in_reverse_order_do_not_confirm_a_cycle(self):
        complete, partial = SignalCycles(), SignalCycles()
        for signal in (True, False):
            complete.observe(signal)
        for signal in (False, True):
            partial.observe(signal)
        self.assertEqual(complete.status("observed"), "complete")
        self.assertEqual(complete.complete_count, 1)
        self.assertEqual(partial.status("observed"), "partial")
        self.assertEqual(partial.complete_count, 0)
        self.assertTrue(partial.pending_start)
        self.assertEqual(partial.unpaired_end_count, 1)

    def test_duplicates_do_not_create_additional_cycles(self):
        cycles = SignalCycles()
        for signal in (True, True, False):
            cycles.observe(signal)
        self.assertEqual(
            cycles.counts(),
            {
                "complete_count": 1,
                "pending_start": False,
                "unpaired_end_count": 0,
                "duplicate_signal_count": 1,
            },
        )
        self.assertEqual(cycles.status("observed"), "complete")

    def test_complete_cycles_do_not_hide_partial_edges(self):
        cycles = SignalCycles()
        for signal in (False, False, True, False, True, False, True):
            cycles.observe(signal)
        self.assertEqual(cycles.complete_count, 2)
        self.assertEqual(cycles.unpaired_end_count, 2)
        self.assertEqual(cycles.duplicate_signal_count, 1)
        self.assertTrue(cycles.pending_start)
        self.assertEqual(cycles.status("observed"), "partial")

    def test_failed_connection_overrides_completed_cycles(self):
        cycles = SignalCycles()
        cycles.observe(True)
        cycles.observe(False)
        self.assertEqual(cycles.status("failed"), "failed")
        self.assertEqual(cycles.status("not-tested"), "not-tested")
        self.assertEqual(cycles.status("no-events"), "no-events")


class EventCycleIntegrationTests(unittest.TestCase):
    def test_independent_fragmented_streams_only_report_sanitized_counts(self):
        real_popen = subprocess.Popen
        children = []

        def spawn(argv, **kwargs):
            if "org.gnome.ScreenSaver" in argv:
                lines = [
                    "unrelated-private-content",
                    "/org/gnome/ScreenSaver: org.gnome.ScreenSaver.ActiveChanged (true,)",
                    "/org/gnome/ScreenSaver: org.gnome.ScreenSaver.ActiveChanged (true,)",
                    "/org/gnome/ScreenSaver: org.gnome.ScreenSaver.ActiveChanged (false,)",
                ]
            else:
                lines = [
                    "/org/freedesktop/login1: "
                    "org.freedesktop.login1.Manager.PrepareForSleep (false,)",
                    "/org/freedesktop/login1: "
                    "org.freedesktop.login1.Manager.PrepareForSleep (true,)",
                ]
            payload = "\n".join(lines) + "\n"
            child = real_popen(
                [
                    sys.executable,
                    "-u",
                    "-c",
                    "import sys,time; "
                    f"payload={payload!r}; "
                    "sys.stdout.write(payload[:31]); sys.stdout.flush(); time.sleep(0.02); "
                    "sys.stdout.write(payload[31:]); sys.stdout.flush(); time.sleep(10)",
                ],
                **kwargs,
            )
            children.append(child)
            return child

        with (
            patch("digitalmirror.events.subprocess.Popen", side_effect=spawn),
            patch("digitalmirror.events.shutil.which", return_value="/synthetic/bin"),
        ):
            report = watch_events(1, ["gnome-lock", "logind-sleep-interface"])
        sources = report["sources"]
        self.assertEqual(sources["gnome-lock"]["cycle_status"], "complete")
        self.assertEqual(sources["gnome-lock"]["cycles"]["complete_count"], 1)
        self.assertEqual(sources["gnome-lock"]["cycles"]["duplicate_signal_count"], 1)
        self.assertEqual(sources["gnome-lock"]["true_count"], 2)
        self.assertEqual(sources["logind-sleep-interface"]["cycle_status"], "partial")
        self.assertEqual(sources["logind-sleep-interface"]["cycles"]["complete_count"], 0)
        self.assertTrue(sources["logind-sleep-interface"]["cycles"]["pending_start"])
        self.assertNotIn("unrelated-private-content", json.dumps(report))
        self.assertTrue(all(child.poll() is not None for child in children))

    def test_monitor_exit_after_pair_remains_failed(self):
        real_popen = subprocess.Popen
        children = []

        def spawn(argv, **kwargs):
            child = real_popen(
                [
                    sys.executable,
                    "-u",
                    "-c",
                    "print('/org/gnome/ScreenSaver: org.gnome.ScreenSaver.ActiveChanged (true,)'); "
                    "print('/org/gnome/ScreenSaver: org.gnome.ScreenSaver.ActiveChanged (false,)')",
                ],
                **kwargs,
            )
            children.append(child)
            return child

        with (
            patch("digitalmirror.events.subprocess.Popen", side_effect=spawn),
            patch("digitalmirror.events.shutil.which", return_value="/synthetic/bin"),
            patch(
                "digitalmirror.cli.diagnose",
                return_value={
                    "schema_version": 1,
                    "status": "available",
                    "checks": [{"source": "gnome-lock", "status": "available"}],
                    "pending_validation": ["bloqueio/desbloqueio reais"],
                },
            ),
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            self.assertEqual(main(["doctor", "--watch-seconds", "1"]), 1)
        report = json.loads(output.getvalue())
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["status"], "degraded")
        self.assertEqual(report["pending_validation"], ["bloqueio/desbloqueio reais"])
        report = report["event_watch"]
        source = report["sources"]["gnome-lock"]
        self.assertEqual(source["cycles"]["complete_count"], 1)
        self.assertEqual(source["status"], "failed")
        self.assertEqual(source["cycle_status"], "failed")
        self.assertEqual(source["reason"], "monitor-ended")
        self.assertTrue(all(child.poll() is not None for child in children))
