from types import SimpleNamespace

from alf import system


def test_get_uptime_returns_mac_uptime(monkeypatch):
    monkeypatch.setattr(system.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(
        system.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout="{ sec = 1757410000, usec = 0 } Mon Sep  8 10:00:00 2025\n",
        ),
    )
    monkeypatch.setattr(system.time, "time", lambda: 1757413600)

    assert system.get_uptime() == "3600"


def test_get_uptime_returns_none_on_non_mac(monkeypatch):
    monkeypatch.setattr(system.platform, "system", lambda: "Linux")

    assert system.get_uptime() is None


def test_get_uptime_returns_none_when_sysctl_fails(monkeypatch):
    monkeypatch.setattr(system.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(
        system.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=1,
            stdout="",
        ),
    )

    assert system.get_uptime() is None


def test_get_uptime_returns_none_for_invalid_sysctl_output(monkeypatch):
    monkeypatch.setattr(system.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(
        system.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout="not valid sysctl output\n",
        ),
    )

    assert system.get_uptime() is None


def test_get_uptime_returns_none_for_invalid_boot_time(monkeypatch):
    monkeypatch.setattr(system.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(
        system.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout="{ sec = not-a-number, usec = 0 }\n",
        ),
    )

    assert system.get_uptime() is None


def test_get_uptime_returns_none_when_sysctl_unavailable(monkeypatch):
    monkeypatch.setattr(system.platform, "system", lambda: "Darwin")

    def fail_sysctl(*args, **kwargs):
        raise OSError("sysctl unavailable")

    monkeypatch.setattr(system.subprocess, "run", fail_sysctl)

    assert system.get_uptime() is None


def test_get_uptime_returns_none_when_sysctl_times_out(monkeypatch):
    monkeypatch.setattr(system.platform, "system", lambda: "Darwin")

    def timeout_sysctl(*args, **kwargs):
        raise system.subprocess.TimeoutExpired("sysctl", 5)

    monkeypatch.setattr(system.subprocess, "run", timeout_sysctl)

    assert system.get_uptime() is None


def test_get_system_information(monkeypatch):
    monkeypatch.setattr(system.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(system.platform, "node", lambda: "alf-mac")
    monkeypatch.setattr(system.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(system.platform, "python_version", lambda: "3.14.7")
    monkeypatch.setattr(system, "get_uptime", lambda: "3600.0")

    assert system.get_system_information() == {
        "operating_system": "Darwin",
        "hostname": "alf-mac",
        "architecture": "arm64",
        "python_version": "3.14.7",
        "uptime": "3600.0",
    }


def test_get_system_information_survives_unavailable_uptime(monkeypatch):
    monkeypatch.setattr(system.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(system.platform, "node", lambda: "alf-mac")
    monkeypatch.setattr(system.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(system.platform, "python_version", lambda: "3.14.7")
    monkeypatch.setattr(system, "get_uptime", lambda: None)

    assert system.get_system_information() == {
        "operating_system": "Darwin",
        "hostname": "alf-mac",
        "architecture": "arm64",
        "python_version": "3.14.7",
        "uptime": None,
    }


def test_get_capability_describes_system_awareness():
    result = system.get_capability()

    assert result == {
        "id": "system",
        "name": "System awareness",
        "description": "Provides basic information about the system running ALF",
    }
