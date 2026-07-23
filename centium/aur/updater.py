"""Check AUR packages for available updates."""
import subprocess
from centium.aur import rpc


def get_aur_packages() -> list[tuple[str, str]]:
    """Return list of (pkgname, installed_version) for all AUR packages."""
    result = subprocess.run(["pacman", "-Qm"], capture_output=True, text=True)
    packages = []
    for line in result.stdout.splitlines():
        parts = line.strip().split()
        if len(parts) == 2:
            packages.append((parts[0], parts[1]))
    return packages


def _version_newer(installed: str, available: str) -> bool:
    """Basic version comparison — returns True if available is newer."""
    if installed == available:
        return False
    # Use vercmp via pacman if available
    result = subprocess.run(
        ["vercmp", available, installed],
        capture_output=True, text=True
    )
    try:
        return int(result.stdout.strip()) > 0
    except ValueError:
        return available != installed


def check_updates(packages: list[tuple[str, str]]) -> list[dict]:
    """Check AUR for updates to installed packages.
    Returns list of dicts with name, installed, available."""
    updates = []
    # Batch query AUR RPC for all packages at once
    names = [pkg[0] for pkg in packages]
    installed_map = {pkg[0]: pkg[1] for pkg in packages}

    # AUR RPC supports multi-info queries
    import urllib.request
    import urllib.parse
    import json

    chunk_size = 50  # AUR RPC limit per request
    aur_data = {}

    for i in range(0, len(names), chunk_size):
        chunk = names[i:i + chunk_size]
        args = "&".join(f"arg[]={urllib.parse.quote(n)}" for n in chunk)
        url = f"https://aur.archlinux.org/rpc/v5/info?{args}"
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                data = json.loads(r.read())
            for pkg in data.get("results", []):
                aur_data[pkg["Name"]] = pkg
        except Exception:
            continue

    for name, installed_ver in packages:
        if name not in aur_data:
            continue
        available_ver = aur_data[name].get("Version", installed_ver)
        if _version_newer(installed_ver, available_ver):
            updates.append({
                "name":      name,
                "installed": installed_ver,
                "available": available_ver,
            })

    return updates
