"""Identidade de sessão: falhar sem consultar LockedHint de um candidato incorreto."""

import json
import unittest

from test_doctor import X11_ENV, healthy_runner

from digitalmirror.doctor import CommandResult, collect_checks, read_lock_checks
from digitalmirror.session import resolve_session


class SessionValidationTests(unittest.TestCase):
    def test_explicit_candidate_is_validated_without_discovery(self):
        calls = []

        def runner(argv):
            calls.append(argv)
            return healthy_runner(argv)

        result = resolve_session(X11_ENV, runner)
        self.assertIsNone(result.reason)
        self.assertIsNotNone(result.path)
        self.assertFalse(result.from_user_display)
        self.assertTrue(any("GetSession" in call for call in calls))
        self.assertFalse(any("GetUser" in call for call in calls))

    def test_missing_id_uses_only_primary_user_display_and_accepts_screen_suffix(self):
        calls = []
        env = dict(X11_ENV, DISPLAY=":99.0", XDG_SESSION_ID="")

        def runner(argv):
            calls.append(argv)
            return healthy_runner(argv)

        checks = {check.source: check for check in collect_checks(env, runner)}
        self.assertEqual(checks["logind-lock"].status, "available")
        self.assertTrue(checks["logind-lock"].details["resolved_from_user_display"])
        self.assertTrue(any(call[-3:] == ["GetUser", "u", "1001"] for call in calls))
        self.assertFalse(any("GetSession" in call or "ListSessions" in call for call in calls))
        output = json.dumps([check.__dict__ for check in checks.values()])
        for private in ("/session/s1", "_1001", ":99", '"1001"'):
            self.assertNotIn(private, output)

    def test_wrong_identity_never_reads_locked_hint_or_falls_back(self):
        replacements = {
            0: "wrong-id",
            1: [1002, "/org/freedesktop/login1/user/_1002"],
            2: "wayland",
            3: "greeter",
            4: True,
            5: ":98",
        }
        for index, value in replacements.items():
            with self.subTest(property=index):
                calls = []

                def runner(argv, calls=calls, index=index, value=value):
                    calls.append(argv)
                    result = healthy_runner(argv)
                    if argv[-6:] == ["Id", "User", "Type", "Class", "Remote", "Display"]:
                        lines = [json.loads(line) for line in result.output.splitlines()]
                        lines[index]["data"] = value
                        return CommandResult("\n".join(json.dumps(item) for item in lines))
                    return result

                check = read_lock_checks(X11_ENV, runner)[1]
                self.assertEqual(check.reason, "session-identity-mismatch")
                self.assertEqual(check.status, "unavailable")
                self.assertFalse(any("LockedHint" in call or "GetUser" in call for call in calls))

    def test_primary_other_display_does_not_enumerate_sessions(self):
        calls = []

        def runner(argv):
            calls.append(argv)
            result = healthy_runner(argv)
            if argv[-6:] == ["Id", "User", "Type", "Class", "Remote", "Display"]:
                lines = result.output.splitlines()
                lines[-1] = json.dumps({"type": "s", "data": ":98"})
                return CommandResult("\n".join(lines))
            return result

        result = resolve_session(dict(X11_ENV, XDG_SESSION_ID=""), runner)
        self.assertEqual(result.reason, "session-identity-mismatch")
        self.assertFalse(any("GetSession" in call or "ListSessions" in call for call in calls))

    def test_invalid_inputs_do_not_query_logind(self):
        for changes in (
            {"DIGITALMIRROR_HOST_UID": "0"},
            {"DIGITALMIRROR_HOST_UID": "4294967296"},
            {"DIGITALMIRROR_HOST_UID": "invalid"},
            {"XDG_SESSION_TYPE": "wayland"},
            {"DISPLAY": "remote:0"},
            {"XDG_SESSION_ID": "../../private"},
        ):
            calls = []
            result = resolve_session(
                X11_ENV | changes, lambda argv, calls=calls: calls.append(argv)
            )
            self.assertIsNotNone(result.reason)
            self.assertIsNone(result.path)
            self.assertEqual(calls, [])

    def test_missing_primary_session_or_bad_path_is_sanitized(self):
        for candidate in (
            ["", "/"],
            ["s1", "/private/path"],
            ["s1"],
            [1, "private"],
            ["s1", "/org/freedesktop/login1/session/self"],
            ["s1", "/org/freedesktop/login1/session/auto"],
        ):

            def runner(argv, candidate=candidate):
                if "org.freedesktop.login1.User" in argv:
                    return CommandResult(json.dumps({"type": "(so)", "data": candidate}))
                return healthy_runner(argv)

            result = resolve_session(dict(X11_ENV, XDG_SESSION_ID=""), runner)
            self.assertIsNone(result.path)
            self.assertIn(result.reason, {"no-primary-graphical-session", "invalid-response"})
            self.assertNotIn("private", repr(result))

    def test_failures_and_bad_types_do_not_reuse_previous_session(self):
        self.assertIsNotNone(resolve_session(X11_ENV, healthy_runner).path)
        for response in (
            CommandResult(reason="timeout"),
            CommandResult("private-invalid"),
            CommandResult('{"type":"s","data":"private"}'),
            CommandResult("[" * 1200 + "0" + "]" * 1200),
        ):
            result = resolve_session(X11_ENV, lambda argv, response=response: response)
            self.assertIsNone(result.path)
            self.assertIn(result.reason, {"timeout", "invalid-response"})
            self.assertNotIn("private", repr(result))

    def test_struct_boolean_and_string_types_are_strict(self):
        for index, value in (
            (1, [True, "/org/freedesktop/login1/user/_1001"]),
            (4, 0),
            (5, [":99"]),
        ):

            def runner(argv, index=index, value=value):
                result = healthy_runner(argv)
                if argv[-6:] == ["Id", "User", "Type", "Class", "Remote", "Display"]:
                    lines = [json.loads(line) for line in result.output.splitlines()]
                    lines[index]["data"] = value
                    return CommandResult("\n".join(json.dumps(item) for item in lines))
                return result

            self.assertEqual(resolve_session(X11_ENV, runner).reason, "invalid-response")
