"""centium suggest — find complementary packages based on what's installed."""
import subprocess
import shutil
from centium.suggest_data import PAIRINGS


def get_installed() -> set[str]:
    """Get all installed package names."""
    result = subprocess.run(["pacman", "-Qq"], capture_output=True, text=True)
    return set(result.stdout.splitlines())


def get_suggestions(installed: set[str]) -> list[dict]:
    """Return suggestions grouped by trigger."""
    results = []
    for pairing in PAIRINGS:
        triggered_by = [t for t in pairing["triggers"] if t in installed]
        if not triggered_by:
            continue
        missing = [
            (pkg, desc)
            for pkg, desc in pairing["suggests"]
            if pkg not in installed
        ]
        if missing:
            results.append({
                "triggered_by": triggered_by,
                "missing": missing,
            })
    return results
