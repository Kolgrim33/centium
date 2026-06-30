import subprocess
from pathlib import Path


def find_pacnew_files() -> list[str]:
    """Find all .pacnew and .pacsave files on the system."""
    try:
        result = subprocess.run(
            ["find", "/etc", "-name", "*.pacnew", "-o", "-name", "*.pacsave"],
            capture_output=True, text=True, timeout=15,
        )
        return sorted(line for line in result.stdout.splitlines() if line.strip())
    except Exception:
        return []


def find_failed_services() -> list[str]:
    """List currently failed systemd services."""
    try:
        result = subprocess.run(
            ["systemctl", "--failed", "--no-legend", "--plain"],
            capture_output=True, text=True, timeout=10,
        )
        return [line.split()[0] for line in result.stdout.splitlines() if line.strip()]
    except Exception:
        return []


def snapshot() -> dict:
    """Capture current system state relevant to an update's side effects."""
    return {
        "pacnew_files": set(find_pacnew_files()),
        "failed_services": set(find_failed_services()),
    }


def diff_snapshots(before: dict, after: dict) -> dict:
    """Compute what changed between two snapshots."""
    return {
        "new_pacnew_files": sorted(after["pacnew_files"] - before["pacnew_files"]),
        "new_failed_services": sorted(after["failed_services"] - before["failed_services"]),
        "resolved_failed_services": sorted(before["failed_services"] - after["failed_services"]),
    }


def kernel_was_updated(updated_packages: list[str]) -> bool:
    kernel_pkgs = {"linux", "linux-lts", "linux-zen", "linux-hardened"}
    return any(pkg in kernel_pkgs for pkg in updated_packages)
