"""Associação por VT: rejeição conservadora antes de LockedHint."""

import json
import unittest

from test_doctor import X11_ENV, healthy_runner

from digitalmirror.doctor import CommandResult, diagnose, read_lock_checks
from digitalmirror.session import IDENTITY_PROPERTIES, SEAT0_PATH, VT_PROPERTIES, resolve_session


def encoded(values):
    return CommandResult("\n".join(json.dumps({"type": t, "data": v}) for t, v in values))


def vt_runner(argv):
    vt = [("u", 7), ("(so)", ["seat0", SEAT0_PATH]), ("b", True)]
    if argv == ["xprop", "-root", "XFree86_VT"]:
        return CommandResult("XFree86_VT(INTEGER) = 7")
    if argv[-1] == "ActiveSession":
        return encoded([("(so)", ["s1", "/org/freedesktop/login1/session/s1"])])
    if argv[-9:] == IDENTITY_PROPERTIES + VT_PROPERTIES:
        base = vt_runner(argv[:-9] + IDENTITY_PROPERTIES)
        return CommandResult(base.output + "\n" + encoded(vt).output)
    if argv[-3:] == VT_PROPERTIES:
        return encoded(vt)
    result = healthy_runner(argv)
    if argv[-6:] == IDENTITY_PROPERTIES:
        lines = result.output.splitlines()
        lines[-1] = json.dumps({"type": "s", "data": ""})
        return CommandResult("\n".join(lines))
    return result


class VTAssociationTests(unittest.TestCase):
    def test_success_keeps_display_empty_and_reads_hint_only_after_revalidation(self):
        for explicit in ("s1", ""):
            with self.subTest(explicit=bool(explicit)):
                calls = []

                def runner(argv, calls=calls):
                    calls.append(argv)
                    return vt_runner(argv)

                report = diagnose(env=dict(X11_ENV, XDG_SESSION_ID=explicit), runner=runner)
                check = next(c for c in report["checks"] if c["source"] == "logind-lock")
                self.assertEqual(check["status"], "available")
                details = check["details"]
                self.assertTrue(details["session_validated"])
                self.assertEqual(details["session_association_source"], "x11-vt")
                self.assertTrue(details["vt_association_attempted"])
                self.assertFalse(details["identity_display_matches"])
                self.assertEqual(details["session_display_status"], "empty")
                self.assertFalse(details["active"])
                for key in (
                    "identity_vt_positive",
                    "identity_seat_supported",
                    "identity_session_active",
                    "identity_vt_matches",
                    "identity_seat_session_matches",
                    "identity_revalidation_matches",
                    "identity_x11_vt_stable",
                ):
                    self.assertIs(details[key], True)
                hint_index = next(i for i, call in enumerate(calls) if call[-1] == "LockedHint")
                self.assertEqual(calls[hint_index - 1][-1], "ActiveSession")
                self.assertEqual(calls.count(["xprop", "-root", "XFree86_VT"]), 2)
                self.assertFalse(
                    any("ListSessions" in call or "TakeControl" in call for call in calls)
                )
                self.assertEqual(sum("GetUser" in call for call in calls), int(not explicit))
                self.assertEqual(sum("GetSession" in call for call in calls), int(bool(explicit)))
                for private in ("/session/s1", SEAT0_PATH, "_1001", ":99", "XFree86_VT(INTEGER)"):
                    self.assertNotIn(private, json.dumps(report))

    def test_display_matching_path_does_not_issue_vt_queries(self):
        calls = []

        def runner(argv):
            calls.append(argv)
            return healthy_runner(argv)

        result = resolve_session(X11_ENV, runner)
        self.assertEqual(result.diagnostics["session_association_source"], "session-display")
        self.assertFalse(result.diagnostics["vt_association_attempted"])
        self.assertFalse(any("XFree86_VT" in call or "ActiveSession" in call for call in calls))

    def test_other_identity_or_nonempty_display_never_attempts_vt(self):
        for index, value in (
            (0, "other"),
            (1, [1002, "/org/freedesktop/login1/user/_1002"]),
            (2, "wayland"),
            (3, "greeter"),
            (4, True),
            (5, ":98"),
            (5, "invalid"),
        ):
            with self.subTest(index=index, value=value):
                calls = []

                def runner(argv, index=index, value=value, calls=calls):
                    calls.append(argv)
                    result = vt_runner(argv)
                    if argv[-6:] == IDENTITY_PROPERTIES:
                        lines = [json.loads(line) for line in result.output.splitlines()]
                        lines[index]["data"] = value
                        return CommandResult("\n".join(json.dumps(line) for line in lines))
                    return result

                check = read_lock_checks(X11_ENV, runner)[1]
                self.assertEqual(check.reason, "session-identity-mismatch")
                self.assertFalse(check.details["vt_association_attempted"])
                self.assertFalse(any("LockedHint" in c or "XFree86_VT" in c for c in calls))

    def test_vt_seat_and_activity_fail_closed(self):
        for index, value, reason in (
            (0, 0, "session-identity-mismatch"),
            (0, True, "invalid-response"),
            (0, -1, "invalid-response"),
            (0, 2**32, "invalid-response"),
            (1, ["seat1", "/org/freedesktop/login1/seat/seat1"], "session-identity-mismatch"),
            (1, ["seat0", "/private/path"], "session-identity-mismatch"),
            (1, ["seat0"], "invalid-response"),
            (1, [1, SEAT0_PATH], "invalid-response"),
            (2, False, "session-identity-mismatch"),
            (2, 1, "invalid-response"),
        ):
            with self.subTest(index=index, value=value):
                calls = []

                def runner(argv, index=index, value=value, calls=calls):
                    calls.append(argv)
                    result = vt_runner(argv)
                    if argv[-3:] == VT_PROPERTIES:
                        lines = [json.loads(line) for line in result.output.splitlines()]
                        lines[index]["data"] = value
                        return CommandResult("\n".join(json.dumps(line) for line in lines))
                    return result

                check = read_lock_checks(X11_ENV, runner)[1]
                self.assertEqual(check.reason, reason)
                self.assertFalse(check.details["session_validated"])
                self.assertFalse(any("LockedHint" in c or "XFree86_VT" in c for c in calls))

    def test_x11_vt_missing_invalid_or_different_never_reads_hint(self):
        for response, reason in (
            (CommandResult("XFree86_VT(INTEGER) = 8"), "session-identity-mismatch"),
            (CommandResult("XFree86_VT(INTEGER) = 0"), "invalid-response"),
            (CommandResult("XFree86_VT(INTEGER) = 4294967296"), "invalid-response"),
            (CommandResult("XFree86_VT: no such atom on any window."), "invalid-response"),
            (CommandResult("XFree86_VT(CARDINAL) = 7"), "invalid-response"),
            (CommandResult(reason="timeout"), "timeout"),
        ):
            calls = []

            def runner(argv, response=response, calls=calls):
                calls.append(argv)
                return response if argv == ["xprop", "-root", "XFree86_VT"] else vt_runner(argv)

            check = read_lock_checks(X11_ENV, runner)[1]
            self.assertEqual(check.reason, reason)
            self.assertFalse(any("LockedHint" in call for call in calls))

    def test_seat_active_session_must_match_id_and_path(self):
        for candidate in (
            ["other", "/org/freedesktop/login1/session/s1"],
            ["s1", "/org/freedesktop/login1/session/other"],
            ["", "/"],
            [1, "/private/path"],
            "private-invalid",
        ):
            calls = []

            def runner(argv, candidate=candidate, calls=calls):
                calls.append(argv)
                if argv[-1] == "ActiveSession":
                    return encoded([("(so)", candidate)])
                return vt_runner(argv)

            check = read_lock_checks(X11_ENV, runner)[1]
            self.assertEqual(check.status, "unavailable")
            self.assertFalse(any("LockedHint" in call for call in calls))
            self.assertNotIn("private", repr(check))

    def test_changes_during_revalidation_do_not_read_hint(self):
        for stage in ("identity", "vt", "seat", "active", "x11", "active-session"):
            with self.subTest(stage=stage):
                calls = []
                counters = {"x11": 0, "seat": 0}

                def runner(argv, stage=stage, calls=calls, counters=counters):
                    calls.append(argv)
                    result = vt_runner(argv)
                    if argv == ["xprop", "-root", "XFree86_VT"]:
                        counters["x11"] += 1
                        if stage == "x11" and counters["x11"] == 2:
                            return CommandResult("XFree86_VT(INTEGER) = 8")
                    if argv[-1] == "ActiveSession":
                        counters["seat"] += 1
                        if stage == "active-session" and counters["seat"] == 2:
                            return encoded([("(so)", ["", "/"])])
                    if argv[-9:] == IDENTITY_PROPERTIES + VT_PROPERTIES:
                        lines = [json.loads(line) for line in result.output.splitlines()]
                        replacements = {
                            "identity": (1, [1002, "/org/freedesktop/login1/user/_1002"]),
                            "vt": (6, 8),
                            "seat": (7, ["seat1", "/private/path"]),
                            "active": (8, False),
                        }
                        if stage in replacements:
                            index, value = replacements[stage]
                            lines[index]["data"] = value
                            return CommandResult("\n".join(json.dumps(line) for line in lines))
                    return result

                check = read_lock_checks(X11_ENV, runner)[1]
                self.assertEqual(check.reason, "session-identity-mismatch")
                self.assertFalse(any("LockedHint" in call for call in calls))
                self.assertNotIn("private", repr(check))

    def test_failures_at_every_query_stage_and_after_success_do_not_reuse_path(self):
        self.assertIsNotNone(resolve_session(X11_ENV, vt_runner).path)
        for failed_step in range(1, 7):
            for failure in (CommandResult(reason="timeout"), CommandResult("private-invalid")):
                calls = []
                counter = [0]

                def runner(argv, calls=calls, counter=counter, step=failed_step, failure=failure):
                    calls.append(argv)
                    if (
                        argv[-3:] == VT_PROPERTIES
                        or argv == ["xprop", "-root", "XFree86_VT"]
                        or argv[-1] == "ActiveSession"
                    ):
                        counter[0] += 1
                        if counter[0] == step:
                            return failure
                    return vt_runner(argv)

                check = read_lock_checks(X11_ENV, runner)[1]
                self.assertEqual(check.reason, failure.reason or "invalid-response")
                self.assertFalse(check.details["session_validated"])
                self.assertFalse(any("LockedHint" in call for call in calls))
                self.assertNotIn("private", repr(check))
