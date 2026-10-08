"""Resolver somente o candidato gráfico explícito ou indicado por logind User.Display."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from digitalmirror.doctor import CommandResult, Runner

SERVICE = "org.freedesktop.login1"
MANAGER = "/org/freedesktop/login1"
SESSION_INTERFACE = SERVICE + ".Session"
USER_INTERFACE = SERVICE + ".User"
BUSCTL = [
    "busctl",
    "--system",
    "--json=short",
    "--auto-start=no",
    "--allow-interactive-authorization=no",
]
SESSION_PATH = re.compile(r"/org/freedesktop/login1/session/[a-zA-Z0-9_]+")
USER_PATH = re.compile(r"/org/freedesktop/login1/user/[a-zA-Z0-9_]+")
SESSION_ID = re.compile(r"[a-zA-Z0-9_-]{1,64}")
IDENTITY_PROPERTIES = ["Id", "User", "Type", "Class", "Remote", "Display"]
VT_PROPERTIES = ["VTNr", "Seat", "Active"]
SEAT0_PATH = "/org/freedesktop/login1/seat/seat0"


@dataclass(frozen=True)
class SessionResolution:
    path: str | None = field(default=None, repr=False)
    reason: str | None = None
    from_user_display: bool = False
    # Somente booleans/enums definidos aqui; nunca propriedades brutas do logind.
    diagnostics: dict[str, bool | str] = field(default_factory=dict)


def json_value(output: str, signature: str) -> object:
    try:
        value = json.loads(output)
    except RecursionError as error:
        raise ValueError("invalid-response") from error
    if not isinstance(value, dict) or value.get("type") != signature or "data" not in value:
        raise ValueError("invalid-response")
    return value["data"]


def local_display(value: str) -> int | None:
    match = re.fullmatch(r":([0-9]{1,6})(?:\.[0-9]{1,6})?", value)
    return int(match[1]) if match else None


def _values(lines: list[str], signatures: tuple[str, ...]) -> list[object]:
    if len(lines) != len(signatures):
        raise ValueError("invalid-response")
    return [json_value(line, signature) for line, signature in zip(lines, signatures, strict=True)]


def _identity(lines: list[str]) -> list[object]:
    values = _values(lines, ("s", "(uo)", "s", "s", "b", "s"))
    session_id, user, session_type, session_class, remote, session_display = values
    if (
        not isinstance(session_id, str)
        or not isinstance(user, list)
        or len(user) != 2
        or type(user[0]) is not int
        or not isinstance(user[1], str)
        or not USER_PATH.fullmatch(user[1])
        or not isinstance(session_type, str)
        or not isinstance(session_class, str)
        or type(remote) is not bool
        or not isinstance(session_display, str)
    ):
        raise ValueError("invalid-response")
    return values


def _vt_identity(lines: list[str]) -> tuple[int, list[str], bool]:
    vt, seat, active = _values(lines, ("u", "(so)", "b"))
    if (
        type(vt) is not int
        or not 0 <= vt < 2**32
        or not isinstance(seat, list)
        or len(seat) != 2
        or not all(isinstance(value, str) for value in seat)
        or type(active) is not bool
    ):
        raise ValueError("invalid-response")
    return vt, seat, active


def _x11_vt(output: str) -> int:
    match = re.fullmatch(r"XFree86_VT\(INTEGER\) = ([1-9][0-9]{0,9})", output)
    if not match or int(match[1]) >= 2**32:
        raise ValueError("invalid-response")
    return int(match[1])


def _properties(path: str, fields: list[str], runner: Runner) -> CommandResult:
    return runner(BUSCTL + ["get-property", SERVICE, path, SESSION_INTERFACE, *fields])


def _vt_association(
    path: str,
    session_id: str,
    identity: list[object],
    runner: Runner,
    diagnostics: dict[str, bool | str],
) -> str | None:
    diagnostics["vt_association_attempted"] = True
    result = _properties(path, VT_PROPERTIES, runner)
    if result.reason:
        return result.reason
    vt, seat, active = _vt_identity(result.output.splitlines())
    checks = {
        "identity_vt_positive": vt > 0,
        "identity_seat_supported": seat == ["seat0", SEAT0_PATH],
        "identity_session_active": active,
    }
    diagnostics.update(checks)
    if not all(checks.values()):
        return "session-identity-mismatch"
    result = runner(["xprop", "-root", "XFree86_VT"])
    if result.reason:
        return result.reason
    x11_vt = _x11_vt(result.output)
    diagnostics["identity_vt_matches"] = x11_vt == vt
    if x11_vt != vt:
        return "session-identity-mismatch"
    seat_query = BUSCTL + ["get-property", SERVICE, SEAT0_PATH, SERVICE + ".Seat", "ActiveSession"]
    result = runner(seat_query)
    if result.reason:
        return result.reason
    seat_session = json_value(result.output, "(so)")
    if (
        not isinstance(seat_session, list)
        or len(seat_session) != 2
        or not all(isinstance(value, str) for value in seat_session)
    ):
        raise ValueError("invalid-response")
    diagnostics["identity_seat_session_matches"] = seat_session == [session_id, path]
    if seat_session != [session_id, path]:
        return "session-identity-mismatch"
    # Releituras reduzem corridas; não representam snapshot atômico.
    result = _properties(path, IDENTITY_PROPERTIES + VT_PROPERTIES, runner)
    if result.reason:
        return result.reason
    lines = result.output.splitlines()
    unchanged = _identity(lines[:6]) == identity and _vt_identity(lines[6:]) == (vt, seat, active)
    diagnostics["identity_revalidation_matches"] = unchanged
    if not unchanged:
        return "session-identity-mismatch"
    result = runner(["xprop", "-root", "XFree86_VT"])
    if result.reason:
        return result.reason
    diagnostics["identity_x11_vt_stable"] = _x11_vt(result.output) == x11_vt
    if not diagnostics["identity_x11_vt_stable"]:
        return "session-identity-mismatch"
    result = runner(seat_query)
    if result.reason:
        return result.reason
    diagnostics["identity_seat_session_matches"] = json_value(result.output, "(so)") == seat_session
    if not diagnostics["identity_seat_session_matches"]:
        return "session-identity-mismatch"
    return None


def resolve_session(env: Mapping[str, str], runner: Runner) -> SessionResolution:
    diagnostics: dict[str, bool | str] = {
        "candidate_source": "not-attempted",
        "session_association_source": "not-validated",
        "vt_association_attempted": False,
    }

    def failure(reason: str) -> SessionResolution:
        return SessionResolution(reason=reason, diagnostics=diagnostics)

    display = local_display(env.get("DISPLAY", ""))
    if env.get("XDG_SESSION_TYPE") != "x11" or display is None:
        return failure("x11-session-not-confirmed")
    explicit = env.get("XDG_SESSION_ID", "")
    host_uid = env.get("DIGITALMIRROR_HOST_UID", "")
    if not re.fullmatch(r"[0-9]{1,10}", host_uid) or not 0 < int(host_uid) < 2**32:
        return failure("missing-host-uid" if explicit else "missing-graphical-session-id")
    uid = int(host_uid)
    process_uid = os.getuid()
    diagnostics.update(
        process_uid_is_root=process_uid == 0,
        host_uid_matches_process_uid=uid == process_uid,
    )
    from_user_display = not bool(explicit)
    if explicit and not SESSION_ID.fullmatch(explicit):
        return failure("invalid-session-id")
    method = "GetSession" if explicit else "GetUser"
    diagnostics["candidate_source"] = "explicit-session-id" if explicit else "user-display"
    result = runner(
        BUSCTL
        + [
            "call",
            SERVICE,
            MANAGER,
            SERVICE + ".Manager",
            method,
            "s" if explicit else "u",
            explicit or str(uid),
        ]
    )
    if result.reason:
        return failure(result.reason)
    try:
        data = json_value(result.output, "o")
        if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], str):
            raise ValueError("invalid-response")
        path = data[0]
        if from_user_display:
            if not USER_PATH.fullmatch(path) or path.endswith("/self"):
                raise ValueError("invalid-response")
            result = runner(BUSCTL + ["get-property", SERVICE, path, USER_INTERFACE, "Display"])
            if result.reason:
                return failure(result.reason)
            candidate = json_value(result.output, "(so)")
            if (
                not isinstance(candidate, list)
                or len(candidate) != 2
                or not all(isinstance(item, str) for item in candidate)
            ):
                raise ValueError("invalid-response")
            explicit, path = candidate
            if not explicit:
                return failure("no-primary-graphical-session")
        if (
            not SESSION_ID.fullmatch(explicit)
            or not SESSION_PATH.fullmatch(path)
            or path.rsplit("/", 1)[-1] in {"self", "auto"}
        ):
            raise ValueError("invalid-response")
        result = _properties(path, IDENTITY_PROPERTIES, runner)
        if result.reason:
            return failure(result.reason)
        values = _identity(result.output.splitlines())
        session_id, user, session_type, session_class, remote, session_display = values
        assert isinstance(session_id, str) and isinstance(user, list)
        assert isinstance(session_display, str)
        observed_display = local_display(session_display)
        identity_checks = {
            "identity_id_matches": session_id == explicit,
            "identity_uid_matches": user[0] == uid,
            "identity_type_x11": session_type == "x11",
            "identity_class_user": session_class == "user",
            "identity_remote_false": remote is False,
            "identity_display_matches": observed_display == display,
        }
        diagnostics.update(identity_checks)
        diagnostics["session_display_status"] = (
            "empty"
            if not session_display
            else "local"
            if observed_display is not None
            else "nonlocal-or-invalid"
        )
        if not all(
            value for key, value in identity_checks.items() if key != "identity_display_matches"
        ):
            return failure("session-identity-mismatch")
        if identity_checks["identity_display_matches"]:
            diagnostics["session_association_source"] = "session-display"
        elif session_display:
            return failure("session-identity-mismatch")
        else:
            reason = _vt_association(path, session_id, values, runner, diagnostics)
            if reason:
                return failure(reason)
            diagnostics["session_association_source"] = "x11-vt"
    except (ValueError, TypeError):
        return failure("invalid-response")
    return SessionResolution(
        path=path, from_user_display=from_user_display, diagnostics=diagnostics
    )
