"""Regressões dos launchers: UID rootless e preflight sem expor a sessão."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ComposeLauncherTests(unittest.TestCase):
    def setUp(self):
        # Docker rootless monta /tmp com noexec; stubs executáveis usam o workspace.
        self.temporary = tempfile.TemporaryDirectory(prefix=".compose-test-", dir=ROOT / "tests")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.marker = self.directory / "docker-called"
        docker = self.directory / "docker"
        docker.write_text(
            "#!/bin/sh\n"
            'touch "$FAKE_DOCKER_MARKER"\n'
            'if [ "$1" = info ]; then\n'
            "  printf '%s\\n' \"${FAKE_SECURITY_OPTIONS:-[]}\"\n"
            "  exit 0\n"
            "fi\n"
            'printf \'%s:%s\\n\' "$DIGITALMIRROR_UID" "$DIGITALMIRROR_GID"\n'
            "printf '%s\\n' \"$@\"\n"
        )
        docker.chmod(0o755)
        identity = self.directory / "id"
        identity.write_text('#!/bin/sh\ncase "$1" in -u) echo 1001;; -g) echo 1002;; esac\n')
        identity.chmod(0o755)
        self.environment = {
            "PATH": str(self.directory) + ":" + os.environ["PATH"],
            "FAKE_DOCKER_MARKER": str(self.marker),
        }

    def launch(self, script, arguments, extra=None):
        return subprocess.run(
            ["sh", str(ROOT / "scripts" / script), *arguments],
            env=self.environment | (extra or {}),
            capture_output=True,
            text=True,
            check=False,
        )

    def test_rootful_maps_host_identity_and_preserves_arguments(self):
        result = self.launch("compose", ["run", "--rm", "dev", "digitalmirror", "doctor"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.splitlines(),
            [
                "1001:1002",
                "compose",
                "-f",
                "compose.yaml",
                "run",
                "--rm",
                "dev",
                "digitalmirror",
                "doctor",
            ],
        )

    def test_rootless_maps_uid_zero_to_unprivileged_host_user(self):
        result = self.launch(
            "compose",
            ["config", "--quiet"],
            {
                "FAKE_SECURITY_OPTIONS": '["name=rootless","name=seccomp,profile=builtin"]',
            },
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines()[0], "0:0")

    def test_desktop_rejects_no_session_and_wayland_before_docker(self):
        for environment in ({}, {"XDG_SESSION_TYPE": "wayland", "DISPLAY": ":99"}):
            with self.subTest(environment=environment):
                result = self.launch("compose-desktop", ["config", "--quiet"], environment)
                self.assertEqual(result.returncode, 2)
                self.assertIn("GNOME/X11", result.stderr)
                self.assertFalse(self.marker.exists())

    def test_desktop_does_not_guess_display_or_xauthority(self):
        environment = {"XDG_SESSION_TYPE": "x11"}
        result = self.launch("compose-desktop", ["run", "--rm", "desktop"], environment)
        self.assertEqual(result.returncode, 2)
        self.assertIn("DISPLAY", result.stderr)
        environment |= {
            "DISPLAY": ":99",
            "XDG_SESSION_ID": "synthetic",
            "XDG_RUNTIME_DIR": str(self.directory),
        }
        result = self.launch("compose-desktop", ["run", "--rm", "desktop"], environment)
        self.assertEqual(result.returncode, 2)
        self.assertIn("XAUTHORITY", result.stderr)
        self.assertFalse(self.marker.exists())

    def test_desktop_rejects_a_file_as_session_bus_without_creating_socket_directory(self):
        authority = self.directory / "synthetic-authority"
        authority.write_text("synthetic")
        (self.directory / "bus").touch()
        result = self.launch(
            "compose-desktop",
            ["config", "--quiet"],
            {
                "XDG_SESSION_TYPE": "x11",
                "DISPLAY": ":99",
                "XDG_SESSION_ID": "synthetic",
                "XDG_RUNTIME_DIR": str(self.directory),
                "XAUTHORITY": str(authority),
            },
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("Socket D-Bus", result.stderr)
        self.assertFalse(self.marker.exists())
