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


def package_why(pkg: str) -> dict | None:
    """Get full context for why a package is installed."""
    _require_pacman()
    result = subprocess.run(["pacman", "-Qi", pkg], capture_output=True, text=True)
    if result.returncode != 0:
        return None

    info = {}
    for line in result.stdout.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            info[key.strip()] = value.strip()

    # reverse dependencies via pactree
    dependents = []
    if shutil.which("pactree"):
        pt = subprocess.run(
            ["pactree", "-r", "-l", pkg],
            capture_output=True, text=True
        )
        dependents = [
            l.strip() for l in pt.stdout.splitlines()
            if l.strip() and l.strip() != pkg
        ]

    # check if currently running
    running = False
    try:
        # get files owned by package
        files_result = subprocess.run(
            ["pacman", "-Ql", pkg],
            capture_output=True, text=True
        )
        # look for binaries in /usr/bin
        binaries = []
        for line in files_result.stdout.splitlines():
            parts = line.split(None, 1)
            if len(parts) == 2:
                path = parts[1].strip()
                if path.startswith("/usr/bin/") and not path.endswith("/"):
                    binaries.append(path.split("/")[-1])

        # check if any binary is running via pgrep
        for binary in binaries:
            pr = subprocess.run(
                ["pgrep", "-x", binary],
                capture_output=True, text=True
            )
            if pr.returncode == 0:
                running = True
                break
    except Exception:
        pass

    # install reason
    reason = info.get("Install Reason", "")
    if "explicitly" in reason.lower():
        install_reason = "explicitly installed by you"
    else:
        install_reason = "installed as a dependency"

    # days since install
    install_date_str = info.get("Install Date", "")
    days_ago = None
    try:
        from datetime import datetime, timezone
        # format: "Fri 26 Jun 2026 09:02:08 PM CAT"
        # strip timezone name and parse
        parts = install_date_str.rsplit(" ", 1)
        dt = datetime.strptime(parts[0].strip(), "%a %d %b %Y %I:%M:%S %p")
        days_ago = (datetime.now() - dt).days
    except Exception:
        pass

    return {
        "name":           info.get("Name", pkg),
        "version":        info.get("Version", "?"),
        "description":    info.get("Description", ""),
        "install_reason": install_reason,
        "install_date":   install_date_str,
        "days_ago":       days_ago,
        "size":           info.get("Installed Size", "?"),
        "dependents":     dependents,
        "running":        running,
        "required_by":    info.get("Required By", "None"),
    }


def package_info_deep(pkg: str) -> dict | None:
    """Get deep info for an installed package via pacman -Qii and -Ql."""
    _require_pacman()

    # Get detailed info
    result = subprocess.run(["pacman", "-Qii", pkg], capture_output=True, text=True)
    if result.returncode != 0:
        return None

    info = {}
    current_key = None
    current_value = []

    for line in result.stdout.splitlines():
        if ":" in line and not line.startswith(" "):
            if current_key:
                info[current_key] = " ".join(current_value).strip()
            key, _, value = line.partition(":")
            current_key = key.strip()
            current_value = [value.strip()]
        elif line.startswith(" ") and current_key:
            current_value.append(line.strip())

    if current_key:
        info[current_key] = " ".join(current_value).strip()

    # Get file list
    files_result = subprocess.run(["pacman", "-Ql", pkg], capture_output=True, text=True)
    files = []
    binaries = []
    configs = []
    man_pages = []

    for line in files_result.stdout.splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2:
            path = parts[1].strip()
            files.append(path)
            if path.startswith("/usr/bin/") and not path.endswith("/"):
                binaries.append(path)
            elif path.startswith("/etc/") and not path.endswith("/"):
                configs.append(path)
            elif "/man/" in path and not path.endswith("/"):
                man_pages.append(path)

    # Get reverse dependencies
    dependents = []
    if shutil.which("pactree"):
        pt = subprocess.run(
            ["pactree", "-r", "-l", pkg],
            capture_output=True, text=True
        )
        dependents = [
            l.strip() for l in pt.stdout.splitlines()
            if l.strip() and l.strip() != pkg
        ]

    # Check if running
    running = False
    for binary in binaries:
        cmd = binary.split("/")[-1]
        pr = subprocess.run(["pgrep", "-x", cmd], capture_output=True, text=True)
        if pr.returncode == 0:
            running = True
            break

    return {
        "name":           info.get("Name", pkg),
        "version":        info.get("Version", "?"),
        "description":    info.get("Description", ""),
        "url":            info.get("URL", ""),
        "licenses":       info.get("Licenses", ""),
        "depends_on":     info.get("Depends On", "None"),
        "optional_deps":  info.get("Optional Deps", "None"),
        "required_by":    info.get("Required By", "None"),
        "install_size":   info.get("Installed Size", "?"),
        "install_date":   info.get("Install Date", "?"),
        "install_reason": info.get("Install Reason", "?"),
        "packager":       info.get("Packager", "?"),
        "build_date":     info.get("Build Date", "?"),
        "backup_files":   info.get("Backup Files", "None"),
        "total_files":    len(files),
        "binaries":       binaries,
        "configs":        configs,
        "man_pages":      man_pages,
        "dependents":     dependents,
        "running":        running,
    }
