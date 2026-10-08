"""Identidade de sessão: falhar sem consultar LockedHint de um candidato incorreto."""

import json
import unittest
from unittest.mock import patch

from test_doctor import X11_ENV, healthy_runner

from digitalmirror.doctor import CommandResult, collect_checks, diagnose, read_lock_checks
from digitalmirror.session import resolve_session

IDENTITY_FIELDS = (
    "identity_id_matches",
    "identity_uid_matches",
    "identity_type_x11",
    "identity_class_user",
    "identity_remote_false",
    "identity_display_matches",
)


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
        self.assertEqual(result.diagnostics["candidate_source"], "explicit-session-id")
        self.assertTrue(all(result.diagnostics[key] is True for key in IDENTITY_FIELDS))
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
        self.assertEqual(checks["logind-lock"].details["candidate_source"], "user-display")
        self.assertEqual(checks["logind-lock"].details["session_display_status"], "local")
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
                self.assertEqual(check.details["candidate_source"], "explicit-session-id")
                self.assertFalse(check.details["session_validated"])
                self.assertEqual(
                    {key: check.details[key] for key in IDENTITY_FIELDS},
                    {key: position != index for position, key in enumerate(IDENTITY_FIELDS)},
                )
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
        self.assertEqual(result.diagnostics["candidate_source"], "user-display")
        self.assertFalse(result.from_user_display)
        self.assertFalse(result.diagnostics["identity_display_matches"])
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
            self.assertEqual(result.diagnostics["candidate_source"], "not-attempted")
            self.assertFalse(any(key in result.diagnostics for key in IDENTITY_FIELDS))

    def test_multiple_mismatches_are_reported_without_private_values(self):
        calls = []

        def runner(argv):
            calls.append(argv)
            result = healthy_runner(argv)
            if argv[-6:] == ["Id", "User", "Type", "Class", "Remote", "Display"]:
                values = [
                    "private-id",
                    [2345, "/org/freedesktop/login1/user/_2345"],
                    "private-type",
                    "private-class",
                    True,
                    "private-display:12",
                ]
                lines = [json.loads(line) for line in result.output.splitlines()]
                for line, value in zip(lines, values, strict=True):
                    line["data"] = value
                return CommandResult("\n".join(json.dumps(line) for line in lines))
            return result

        report = diagnose(env=dict(X11_ENV, XDG_SESSION_ID=""), runner=runner)
        check = next(check for check in report["checks"] if check["source"] == "logind-lock")
        self.assertEqual(report["status"], "degraded")
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(check["reason"], "session-identity-mismatch")
        self.assertEqual(check["details"]["candidate_source"], "user-display")
        self.assertTrue(all(check["details"][key] is False for key in IDENTITY_FIELDS))
        self.assertEqual(check["details"]["session_display_status"], "nonlocal-or-invalid")
        self.assertFalse(any("LockedHint" in call or "ListSessions" in call for call in calls))
        for private in ("private-", "2345", "/session/s1", ":99", "_1001"):
            self.assertNotIn(private, json.dumps(report))

    def test_display_category_distinguishes_empty_invalid_and_other_local_server(self):
        for display, expected in (
            ("", "empty"),
            ("remote:99", "nonlocal-or-invalid"),
            (":bad", "nonlocal-or-invalid"),
            (":98.0", "local"),
        ):
            with self.subTest(category=expected, display=display):

                def runner(argv, display=display):
                    if argv[-3:] == ["VTNr", "Seat", "Active"]:
                        return CommandResult(
                            "\n".join(
                                json.dumps({"type": kind, "data": value})
                                for kind, value in (("u", 0), ("(so)", ["", "/"]), ("b", False))
                            )
                        )
                    result = healthy_runner(argv)
                    if argv[-6:] == ["Id", "User", "Type", "Class", "Remote", "Display"]:
                        lines = result.output.splitlines()
                        lines[-1] = json.dumps({"type": "s", "data": display})
                        return CommandResult("\n".join(lines))
                    return result

                check = read_lock_checks(X11_ENV, runner)[1]
                self.assertEqual(check.reason, "session-identity-mismatch")
                self.assertEqual(check.details["session_display_status"], expected)
                self.assertFalse(check.details["identity_display_matches"])

    def test_failed_queries_preserve_attempted_source_without_identity_results(self):
        for explicit, source, stages in (
            ("s1", "explicit-session-id", ("GetSession", "Id")),
            ("", "user-display", ("GetUser", "Display", "Id")),
        ):
            for stage in stages:
                for failure in (CommandResult(reason="timeout"), CommandResult("private-invalid")):
                    with self.subTest(source=source, stage=stage, reason=failure.reason):
                        calls = []

                        def runner(argv, stage=stage, failure=failure, calls=calls):
                            calls.append(argv)
                            if stage in argv:
                                return failure
                            return healthy_runner(argv)

                        check = read_lock_checks(dict(X11_ENV, XDG_SESSION_ID=explicit), runner)[1]
                        self.assertEqual(check.reason, failure.reason or "invalid-response")
                        self.assertEqual(check.details["candidate_source"], source)
                        self.assertFalse(check.details["session_validated"])
                        self.assertFalse(any(key in check.details for key in IDENTITY_FIELDS))
                        self.assertNotIn("session_display_status", check.details)
                        self.assertFalse(any("LockedHint" in call for call in calls))
                        self.assertNotIn("private", repr(check))

    def test_process_uid_is_diagnostic_only_and_host_uid_selects_user(self):
        for process_uid in (0, 1001, 1002):
            with (
                self.subTest(process_uid=process_uid),
                patch("digitalmirror.session.os.getuid", return_value=process_uid),
            ):
                calls = []

                def runner(argv, calls=calls):
                    calls.append(argv)
                    return healthy_runner(argv)

                check = read_lock_checks(dict(X11_ENV, XDG_SESSION_ID=""), runner)[1]
                self.assertEqual(check.status, "available")
                self.assertTrue(check.details["identity_uid_matches"])
                self.assertEqual(check.details["process_uid_is_root"], process_uid == 0)
                self.assertEqual(check.details["host_uid_matches_process_uid"], process_uid == 1001)
                self.assertTrue(any(call[-3:] == ["GetUser", "u", "1001"] for call in calls))

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
            self.assertEqual(result.diagnostics["candidate_source"], "user-display")
            self.assertFalse(any(key in result.diagnostics for key in IDENTITY_FIELDS))

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

            result = resolve_session(X11_ENV, runner)
            self.assertEqual(result.reason, "invalid-response")
            self.assertFalse(any(key in result.diagnostics for key in IDENTITY_FIELDS))
