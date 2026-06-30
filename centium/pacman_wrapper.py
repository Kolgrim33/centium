import subprocess
import shutil


class PacmanError(Exception):
    pass


def _require_pacman() -> None:
    if not shutil.which("pacman"):
        raise PacmanError("pacman not found — this tool only works on Arch Linux.")


def search(term: str) -> list[dict]:
    """Search for packages via `pacman -Ss`, parse into structured results."""
    _require_pacman()
    result = subprocess.run(["pacman", "-Ss", term], capture_output=True, text=True)
    lines = result.stdout.splitlines()

    packages = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line and not line.startswith(" "):
            # Format: "repo/name version [installed]"
            header = line.split()
            repo_name = header[0]
            version = header[1] if len(header) > 1 else "?"
            installed = "[installed]" in line
            repo, _, name = repo_name.partition("/")
            desc = ""
            if i + 1 < len(lines) and lines[i + 1].startswith(" "):
                desc = lines[i + 1].strip()
                i += 1
            packages.append({
                "repo": repo,
                "name": name,
                "version": version,
                "installed": installed,
                "description": desc,
            })
        i += 1
    return packages


def package_info(pkg: str) -> dict | None:
    """Get info for a package about to be installed, via `pacman -Si` (repo)
    falling back to local info if already installed. Returns None if not found."""
    _require_pacman()
    result = subprocess.run(["pacman", "-Si", pkg], capture_output=True, text=True)
    if result.returncode != 0:
        return None

    info = {}
    for line in result.stdout.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            info[key.strip()] = value.strip()

    return {
        "name": info.get("Name", pkg),
        "version": info.get("Version", "?"),
        "repo": info.get("Repository", "?"),
        "description": info.get("Description", ""),
        "download_size": info.get("Download Size", "?"),
        "install_size": info.get("Installed Size", "?"),
        "depends_on": info.get("Depends On", "None"),
    }


def would_break_dependents(pkg: str) -> list[str]:
    """Check what installed packages depend on `pkg`, via `pacman -Qi`-style
    reverse dependency lookup (`pacman -Qii` isn't reliable for this, so we
    use the dedicated `pactree -r` if available, else `pacman -Qi`)."""
    _require_pacman()
    if shutil.which("pactree"):
        result = subprocess.run(["pactree", "-r", "-l", pkg], capture_output=True, text=True)
        deps = [line.strip() for line in result.stdout.splitlines() if line.strip() and line.strip() != pkg]
        return deps
    return []


def run_install(pkg: str) -> int:
    """Hand off to the real, interactive pacman for the actual transaction.
    Centium never performs the install itself — it only adds a preview layer."""
    return subprocess.call(["sudo", "pacman", "-S", pkg])


def run_remove(pkg: str) -> int:
    return subprocess.call(["sudo", "pacman", "-R", pkg])


def update_preview() -> list[dict]:
    """Dry-run a sync to see what would be updated, via `pacman -Sup` /
    `checkupdates` if available (checkupdates doesn't touch the live db lock,
    which is safer to call without sudo)."""
    if shutil.which("checkupdates"):
        result = subprocess.run(["checkupdates"], capture_output=True, text=True)
        updates = []
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 4:
                updates.append({
                    "name": parts[0],
                    "old_version": parts[1],
                    "new_version": parts[3],
                })
        return updates
    return []


def run_update() -> int:
    return subprocess.call(["sudo", "pacman", "-Syu"])
