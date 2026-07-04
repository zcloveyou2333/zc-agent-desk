from __future__ import annotations

import os
import platform
import socket
import subprocess
import threading
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / "security" / "macos-hermes.sb"


pytestmark = pytest.mark.skipif(
    platform.system() != "Darwin", reason="sandbox-exec is a macOS-only gate"
)


def sandbox(command: str) -> subprocess.CompletedProcess[str]:
    assert PROFILE.exists(), "the macOS sandbox profile has not been implemented"
    return subprocess.run(
        [
            "/usr/bin/sandbox-exec",
            "-f",
            str(PROFILE),
            "-D",
            f"WORKSPACE={ROOT}",
            "-D",
            f"USER_HOME={Path.home()}",
            "/bin/sh",
            "-c",
            command,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_policy_allows_workspace_write(tmp_path: Path) -> None:
    target = ROOT / ".sandbox-write-probe"
    target.unlink(missing_ok=True)

    result = sandbox(f"printf allowed > {target}")

    try:
        assert result.returncode == 0, result.stderr
        assert target.read_text() == "allowed"
    finally:
        target.unlink(missing_ok=True)


def test_policy_denies_write_outside_workspace() -> None:
    target = Path("/tmp") / f"zc-agent-desk-denied-{os.getpid()}"
    target.unlink(missing_ok=True)

    result = sandbox(f"printf denied > {target}")

    assert result.returncode != 0
    assert not target.exists()


def test_policy_denies_reading_ssh_directory() -> None:
    result = sandbox(f"ls {Path.home() / '.ssh'}")

    assert result.returncode != 0


def test_policy_allows_loopback_network_for_provider_and_sidecar() -> None:
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]
    accepted = threading.Event()

    def accept_once() -> None:
        try:
            connection, _ = server.accept()
            accepted.set()
            connection.close()
        finally:
            server.close()

    thread = threading.Thread(target=accept_once, daemon=True)
    thread.start()

    result = sandbox(f"/usr/bin/nc -z 127.0.0.1 {port}")

    assert result.returncode == 0, result.stderr
    assert accepted.wait(timeout=1)
