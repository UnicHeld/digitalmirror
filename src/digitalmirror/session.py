"""Resolver somente o candidato gráfico explícito ou indicado por logind User.Display."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from digitalmirror.doctor import Runner

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


def resolve_session(env: Mapping[str, str], runner: Runner) -> SessionResolution:
    diagnostics: dict[str, bool | str] = {"candidate_source": "not-attempted"}

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
        result = runner(
            BUSCTL
            + [
                "get-property",
                SERVICE,
                path,
                SESSION_INTERFACE,
                "Id",
                "User",
                "Type",
                "Class",
                "Remote",
                "Display",
            ]
        )
        if result.reason:
            return failure(result.reason)
        lines = result.output.splitlines()
        if len(lines) != 6:
            raise ValueError("invalid-response")
        values = [
            json_value(line, signature)
            for line, signature in zip(lines, ("s", "(uo)", "s", "s", "b", "s"), strict=True)
        ]
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
        if not all(identity_checks.values()):
            return failure("session-identity-mismatch")
    except (ValueError, TypeError):
        return failure("invalid-response")
    return SessionResolution(
        path=path, from_user_display=from_user_display, diagnostics=diagnostics
    )
