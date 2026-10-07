import contextlib
import io
import json
import subprocess
import sys
import unittest
from unittest.mock import patch

from digitalmirror.cli import main
from digitalmirror.doctor import (
    CommandResult,
    collect_checks,
    diagnose,
    monitor_index,
    parse_active_window,
    parse_boolean,
    parse_geometry,
    parse_idle,
    parse_monitors,
    run_readonly,
)
from digitalmirror.events import parse_signal, watch_events

X11_ENV = {
    "XDG_SESSION_TYPE": "x11",
    "DISPLAY": ":99",
    "DBUS_SESSION_BUS_ADDRESS": "synthetic-bus",
    "XDG_RUNTIME_DIR": "/synthetic/runtime",
    "XDG_SESSION_ID": "s1",
    "DIGITALMIRROR_HOST_UID": "1001",
}
MONITORS = (
    "Monitors: 2\n"
    " 0: +*DISPLAY-A 1920/500x1080/300+0+0  DISPLAY-A\n"
    " 1: +DISPLAY-B 1920/500x1080/300-1920+0  DISPLAY-B"
)


def healthy_runner(argv):
    if argv[:2] == ["xprop", "-root"]:
        return CommandResult("_NET_ACTIVE_WINDOW(WINDOW): window id # 0x1234")
    if argv[0] == "xprop":
        return CommandResult(
            'WM_CLASS(STRING) = "SyntheticPrivateApp", "SyntheticPrivateClass"\n'
            "_NET_WM_PID(CARDINAL) = 123456\n_NET_WM_DESKTOP(CARDINAL) = 0"
        )
    if argv[0] == "xdotool":
        return CommandResult("WINDOW=4660\nX=-1000\nY=0\nWIDTH=900\nHEIGHT=600\nSCREEN=0")
    if argv[0] == "xprintidle":
        return CommandResult("300000")
    if argv[0] == "xrandr":
        return CommandResult(MONITORS)
    if argv[0] == "busctl":
        if "call" in argv:
            path = (
                "/org/freedesktop/login1/user/_1001"
                if "GetUser" in argv
                else "/org/freedesktop/login1/session/s1"
            )
            return CommandResult(json.dumps({"type": "o", "data": [path]}))
        if "org.freedesktop.login1.User" in argv:
            return CommandResult(
                json.dumps({"type": "(so)", "data": ["s1", "/org/freedesktop/login1/session/s1"]})
            )
        if argv[-1] == "LockedHint":
            return CommandResult(json.dumps({"type": "b", "data": False}))
        values = [
            ("s", "s1"),
            ("(uo)", [1001, "/org/freedesktop/login1/user/_1001"]),
            ("s", "x11"),
            ("s", "user"),
            ("b", False),
            ("s", ":99"),
        ]
        return CommandResult(
            "\n".join(json.dumps({"type": kind, "data": value}) for kind, value in values)
        )
    if "introspect" in argv:
        return CommandResult("PrepareForSleep(b start);")
    if "org.freedesktop.login1.Manager.GetSession" in argv:
        return CommandResult("(objectpath '/org/freedesktop/login1/session/s1',)")
    if "org.freedesktop.systemd1.Manager.GetUnit" in argv:
        return CommandResult(
            "(objectpath '/org/freedesktop/systemd1/unit/graphical_2dsession_2etarget',)"
        )
    if "org.freedesktop.DBus.Properties.Get" in argv:
        return CommandResult("(<'active'>,)")
    return CommandResult("(false,)")


class ParserTests(unittest.TestCase):
    def test_active_and_no_focus(self):
        self.assertEqual(
            parse_active_window("_NET_ACTIVE_WINDOW(WINDOW): window id # 0x1234"), "0x1234"
        )
        self.assertIsNone(parse_active_window("_NET_ACTIVE_WINDOW(WINDOW): window id # 0x0"))
        with self.assertRaises(ValueError):
            parse_active_window("_NET_ACTIVE_WINDOW: not found.")

    def test_idle_is_aggregate_milliseconds(self):
        self.assertEqual(parse_idle("300000"), 300000)
        for value in ("-1", "nan", "1.5", "", "unavailable"):
            with self.assertRaises(ValueError):
                parse_idle(value)

    def test_boolean_must_be_exact(self):
        self.assertTrue(parse_boolean("(true,)"))
        self.assertFalse(parse_boolean("b false"))
        for value in ("true", "(false, true)", "('true',)"):
            with self.assertRaises(ValueError):
                parse_boolean(value)

    def test_monitor_geometry_and_primary(self):
        monitors = parse_monitors(MONITORS)
        self.assertEqual(monitors[1], (False, (-1920, 0, 1920, 1080)))
        self.assertEqual(monitor_index((-1000, 0, 900, 600), monitors), 1)
        self.assertEqual(monitor_index((-10, 0, 20, 20), monitors), 0)
        self.assertIsNone(monitor_index((9000, 9000, 20, 20), monitors))
        self.assertEqual(parse_geometry("X=-1\nY=2\nWIDTH=100\nHEIGHT=200"), (-1, 2, 100, 200))
        for value in ("Monitors: 0", "Monitors: 3\n" + MONITORS.split("\n", 1)[1]):
            with self.assertRaises(ValueError):
                parse_monitors(value)
        with self.assertRaises(ValueError):
            parse_geometry("X=0\nY=0\nWIDTH=0\nHEIGHT=200")


class DoctorTests(unittest.TestCase):
    def test_no_display_does_not_attempt_x11_or_session_bus(self):
        calls = []

        def runner(argv):
            calls.append(argv)
            return CommandResult(reason="command-failed")

        checks = collect_checks({}, runner)
        self.assertEqual(len(calls), 1)
        self.assertIn("--system", calls[0])
        self.assertTrue(all(c.status == "unavailable" for c in checks))
        self.assertIn("missing-display", {c.reason for c in checks})

    def test_wayland_not_treated_as_x11(self):
        environment = dict(X11_ENV, XDG_SESSION_TYPE="wayland")
        checks = collect_checks(environment, healthy_runner)
        self.assertEqual(checks[0].reason, "x11-session-not-confirmed")
        self.assertEqual(next(c for c in checks if c.source == "logind-lock").status, "unavailable")

    def test_missing_session_id_and_host_uid_keep_other_sources_without_guessing(self):
        calls = []
        environment = {
            key: value
            for key, value in X11_ENV.items()
            if key not in {"XDG_SESSION_ID", "DIGITALMIRROR_HOST_UID"}
        }

        def runner(argv):
            calls.append(argv)
            return healthy_runner(argv)

        report = diagnose(env=environment, runner=runner)
        checks = {check["source"]: check for check in report["checks"]}
        self.assertEqual(report["status"], "degraded")
        self.assertEqual(checks["logind-lock"]["status"], "unavailable")
        self.assertEqual(checks["logind-lock"]["reason"], "missing-graphical-session-id")
        for source in ("x11-focus", "gnome-lock", "logind-sleep-interface"):
            self.assertEqual(checks[source]["status"], "available")
        self.assertFalse(any("org.freedesktop.login1.Manager.GetSession" in call for call in calls))
        self.assertFalse(any(call[0] == "busctl" for call in calls))

    def test_success_is_read_availability_not_transition_validation(self):
        report = diagnose(env=X11_ENV, runner=healthy_runner)
        self.assertEqual(report["status"], "available")
        self.assertGreater(len(report["pending_validation"]), 0)
        monitor = next(c for c in report["checks"] if c["source"] == "xrandr-monitors")
        self.assertEqual(monitor["details"]["count"], 2)
        self.assertTrue(monitor["details"]["focused_window_assigned"])

    def test_missing_app_does_not_mark_other_sources_missing(self):
        def runner(argv):
            if argv[:2] == ["xprop", "-id"]:
                return CommandResult("WM_CLASS: not found.")
            return healthy_runner(argv)

        checks = {c.source: c for c in collect_checks(X11_ENV, runner)}
        self.assertEqual(checks["window-class"].status, "unavailable")
        self.assertEqual(checks["x11-idle"].status, "available")
        self.assertEqual(checks["gnome-lock"].status, "available")

    def test_graphical_target_reads_host_dbus_without_starting_unit(self):
        calls = []

        def runner(argv):
            calls.append(argv)
            if "org.freedesktop.DBus.Properties.Get" in argv:
                return CommandResult("(<'inactive'>,)")
            return healthy_runner(argv)

        checks = {c.source: c for c in collect_checks(X11_ENV, runner)}
        self.assertEqual(checks["gnome-graphical-target"].reason, "target-inactive")
        self.assertFalse(any(call[0] == "systemctl" for call in calls))
        self.assertFalse(any("StartUnit" in str(call) for call in calls))
        self.assertTrue(any("org.freedesktop.systemd1.Manager.GetUnit" in call for call in calls))

    def test_graphical_target_bad_unit_path_or_failed_property_is_unavailable(self):
        for response in (CommandResult(reason="timeout"), CommandResult("invalid-path")):

            def runner(argv, result=response):
                if "org.freedesktop.systemd1.Manager.GetUnit" in argv:
                    return result
                return healthy_runner(argv)

            checks = {c.source: c for c in collect_checks(X11_ENV, runner)}
            self.assertEqual(checks["gnome-graphical-target"].status, "unavailable")

    def test_timeout_invalid_data_and_missing_tools_are_normalized(self):
        for response in (
            CommandResult(reason="timeout"),
            CommandResult(reason="missing-command"),
            CommandResult(output="private-content-unparseable"),
        ):
            checks = collect_checks(X11_ENV, lambda argv, result=response: result)
            self.assertTrue(all(c.status == "unavailable" for c in checks))
            self.assertNotIn("private-content", json.dumps([c.__dict__ for c in checks]))

    def test_no_title_query_or_mutating_command_and_no_metadata_in_report(self):
        calls = []

        def runner(argv):
            calls.append(argv)
            return healthy_runner(argv)

        output = json.dumps(diagnose(env=X11_ENV, runner=runner))
        for value in (
            "SyntheticPrivate",
            "123456",
            "0x1234",
            "DISPLAY-A",
            "DISPLAY-B",
            "synthetic-bus",
            "/synthetic/runtime",
            "/session/s1",
        ):
            self.assertNotIn(value, output)
        for call in calls:
            self.assertNotIn("_NET_WM_NAME", call)
            self.assertNotIn("WM_NAME", call)
            if call[0] == "xdotool":
                self.assertEqual(call[1], "getwindowgeometry")
            if call[0] == "xrandr":
                self.assertEqual(call[1:], ["--listactivemonitors"])

    def test_limits_reject_nan_infinity_and_unbounded_run(self):
        for samples, interval in (
            (0, 5),
            (721, 5),
            (1, 0),
            (1, float("nan")),
            (1, float("inf")),
            (1, 61),
        ):
            with self.assertRaises(ValueError):
                diagnose(samples, interval, runner=healthy_runner)

    def test_recovery_preserves_failure_counts_and_degraded_status(self):
        attempts = 0

        def runner(argv):
            nonlocal attempts
            if argv[:2] == ["xprop", "-root"]:
                attempts += 1
                if attempts == 1:
                    return CommandResult(reason="timeout")
            return healthy_runner(argv)

        with patch("digitalmirror.doctor.time.sleep"):
            report = diagnose(2, env=X11_ENV, runner=runner)
        self.assertEqual(report["status"], "degraded")
        self.assertEqual(
            report["source_status_counts"]["x11-focus"], {"available": 1, "unavailable": 1}
        )
        self.assertEqual(report["source_reason_counts"]["x11-focus"]["timeout"], 1)

    def test_cli_json_and_exit_codes(self):
        with (
            patch.dict("os.environ", {}, clear=True),
            patch("digitalmirror.doctor.shutil.which", return_value=None),
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            self.assertEqual(main(["doctor"]), 1)
            self.assertEqual(json.loads(output.getvalue())["schema_version"], 1)
        for arguments in (["doctor", "--interval", "nan"], ["doctor", "--watch-seconds", "901"]):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                main(arguments)
            self.assertEqual(error.exception.code, 2)


class ProcessTests(unittest.TestCase):
    def test_real_child_failure_does_not_expose_stderr(self):
        result = run_readonly(
            [sys.executable, "-c", "import sys; print('private', file=sys.stderr); sys.exit(7)"]
        )
        self.assertEqual(result, CommandResult(reason="command-failed"))

    def test_output_limit_and_timeout_kill_child(self):
        result = run_readonly([sys.executable, "-c", "print('a'*70000)"])
        self.assertEqual(result.reason, "output-too-large")
        with patch("digitalmirror.doctor.TIMEOUT_SECONDS", 0.05):
            result = run_readonly([sys.executable, "-c", "import time; time.sleep(10)"])
        self.assertEqual(result.reason, "timeout")

    def test_no_runtime_dependencies_module_entrypoint(self):
        result = subprocess.run(
            [sys.executable, "-m", "digitalmirror", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("doctor", result.stdout)


class EventTests(unittest.TestCase):
    def test_stream_counts_and_child_cleanup(self):
        real_popen = subprocess.Popen
        children = []

        def spawn(argv, **kwargs):
            child = real_popen(
                [
                    sys.executable,
                    "-u",
                    "-c",
                    "import time; "
                    "print('/org/gnome/ScreenSaver: org.gnome.ScreenSaver.ActiveChanged (true,)'); "
                    "print('/org/gnome/ScreenSaver: org.gnome.ScreenSaver.ActiveChanged (false,)');"
                    "time.sleep(10)",
                ],
                **kwargs,
            )
            children.append(child)
            return child

        with (
            patch("digitalmirror.events.subprocess.Popen", side_effect=spawn),
            patch("digitalmirror.events.shutil.which", return_value="/synthetic/bin"),
        ):
            report = watch_events(1, ["gnome-lock"], env={})
        source = report["sources"]["gnome-lock"]
        self.assertEqual(source["status"], "observed")
        self.assertEqual(source["true_count"], 1)
        self.assertEqual(source["false_count"], 1)
        self.assertEqual(source["cycle_status"], "complete")
        self.assertEqual(source["cycles"]["complete_count"], 1)
        self.assertTrue(all(child.poll() is not None for child in children))

    def test_only_expected_signal_booleans_are_parsed(self):
        self.assertEqual(
            parse_signal(
                "logind-sleep-interface",
                "/org/freedesktop/login1: org.freedesktop.login1.Manager.PrepareForSleep (true,)",
            ),
            "true",
        )
        self.assertEqual(
            parse_signal(
                "gnome-lock", "/org/gnome/ScreenSaver: org.gnome.ScreenSaver.ActiveChanged (false,)"
            ),
            "false",
        )
        self.assertIsNone(parse_signal("gnome-lock", "unrelated-private-output"))
        self.assertIsNone(
            parse_signal(
                "gnome-lock", "unrelated-property: org.gnome.ScreenSaver.ActiveChanged (true,)"
            )
        )

    def test_no_available_source_starts_no_monitor(self):
        with patch("digitalmirror.events.subprocess.Popen") as spawn:
            report = watch_events(1, [])
        spawn.assert_not_called()
        self.assertTrue(all(c["status"] == "not-tested" for c in report["sources"].values()))
        for source in report["sources"].values():
            self.assertEqual(source["cycle_status"], "not-tested")
            self.assertEqual(source["cycles"]["complete_count"], 0)
            self.assertFalse(source["cycles"]["pending_start"])

    def test_missing_binary_and_watch_limits(self):
        with patch("digitalmirror.events.shutil.which", return_value=None):
            report = watch_events(1, ["gnome-lock"])
        self.assertEqual(report["sources"]["gnome-lock"]["reason"], "missing-command")
        for seconds in (0, 901):
            with self.assertRaises(ValueError):
                watch_events(seconds, [])
