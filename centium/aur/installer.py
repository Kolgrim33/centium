"""High level AUR install flow with AUR dependency resolution."""
import re
import subprocess
from centium.aur import rpc, builder


def _in_pacman(pkgname: str) -> bool:
    """Check if a package is available in official repos or already installed."""
    result = subprocess.run(
        ["pacman", "-Si", pkgname],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        return True
    result = subprocess.run(
        ["pacman", "-Qi", pkgname],
        capture_output=True, text=True
    )
    return result.returncode == 0


def _in_aur(pkgname: str) -> bool:
    """Check if a package exists in the AUR."""
    try:
        return rpc.info(pkgname) is not None
    except rpc.AURError:
        return False


def _strip_version(dep: str) -> str:
    """Strip version constraints from dep string e.g. python>=3.11 -> python."""
    return re.split(r"[><=!]", dep)[0].strip()


def resolve_aur_deps(pkg: dict, print_fn, visited: set[str] | None = None) -> list[str]:
    """Recursively find AUR deps that need to be installed first.
    Returns ordered list of AUR pkgnames to install before the main package."""
    if visited is None:
        visited = set()

    pkgname = pkg.get("Name", "")
    if pkgname in visited:
        return []
    visited.add(pkgname)

    aur_deps = []
    all_deps = pkg.get("Depends", []) + pkg.get("MakeDepends", [])

    for raw_dep in all_deps:
        dep = _strip_version(raw_dep)
        if _in_pacman(dep):
            continue
        dep_info = rpc.info(dep)
        if dep_info is None:
            continue
        print_fn(f"  [dim]AUR dep detected: {dep}[/dim]")
        sub_deps = resolve_aur_deps(dep_info, print_fn, visited)
        aur_deps.extend(sub_deps)
        aur_deps.append(dep)

    return aur_deps


def install(pkgname: str, confirm_fn, print_fn, warn_fn, error_fn,
            _visited: set[str] | None = None) -> int:
    """Full AUR install pipeline with recursive AUR dependency resolution."""

    if _visited is None:
        _visited = set()
    if pkgname in _visited:
        print_fn(f"[dim]Already processed {pkgname}, skipping.[/dim]")
        return 0
    _visited.add(pkgname)

    # 1. Fetch package info
    print_fn(f"\n[dim]Searching AUR for '{pkgname}'...[/dim]")
    try:
        pkg = rpc.info(pkgname)
    except rpc.AURError as e:
        error_fn(str(e))
        return 1

    if pkg is None:
        error_fn(f"'{pkgname}' not found in AUR.")
        return 1

    # 2. Show preview
    print_fn(f"\n[bold]{pkg['Name']}[/bold]  [dim]AUR package[/dim]")
    print_fn(f"  [dim]{'description':<18}[/dim]{pkg.get('Description', '—')}")
    print_fn(f"  [dim]{'version':<18}[/dim]{pkg.get('Version', '?')}")
    print_fn(f"  [dim]{'maintainer':<18}[/dim]{pkg.get('Maintainer', '?')}")
    print_fn(f"  [dim]{'votes':<18}[/dim]{pkg.get('NumVotes', 0)}")
    print_fn(f"  [dim]{'popularity':<18}[/dim]{pkg.get('Popularity', 0):.4f}")

    deps = pkg.get("Depends", [])
    if deps:
        print_fn(f"  [dim]{'depends on':<18}[/dim]{', '.join(deps)}")
    print_fn("")

    # 3. Resolve AUR dependencies
    print_fn("[dim]Checking dependencies...[/dim]")
    try:
        aur_deps = resolve_aur_deps(pkg, print_fn)
    except Exception as e:
        warn_fn(f"Dependency resolution failed: {e}")
        aur_deps = []

    if aur_deps:
        print_fn(f"\n[yellow]The following AUR dependencies need to be installed first:[/yellow]")
        for dep in aur_deps:
            print_fn(f"  [dim]•[/dim] {dep}")
        print_fn("")
        if not confirm_fn("Install AUR dependencies first?"):
            print_fn("[dim]Cancelled.[/dim]")
            return 0
        for dep in aur_deps:
            print_fn(f"\n[dim]Installing AUR dependency: {dep}[/dim]")
            rc = install(dep, confirm_fn, print_fn, warn_fn, error_fn, _visited)
            if rc != 0:
                error_fn(f"Failed to install AUR dependency: {dep}")
                return rc

    # 4. Clone
    pkgbase = pkg.get("PackageBase", pkgname)
    clone_url = rpc.clone_url(pkgbase)
    print_fn(f"[dim]Cloning {clone_url}...[/dim]")
    try:
        pkg_path = builder.clone_or_pull(pkgbase, clone_url)
    except builder.BuildError as e:
        error_fn(str(e))
        return 1

    # 5. Read PKGBUILD
    try:
        pkgbuild_text = builder.read_pkgbuild(pkg_path)
    except builder.BuildError as e:
        error_fn(str(e))
        return 1

    # 6. Security scan
    warnings = builder.scan_pkgbuild(pkgbuild_text)
    if warnings:
        warn_fn(f"{len(warnings)} suspicious pattern(s) found in PKGBUILD:")
        for w in warnings:
            print_fn(f"  [yellow]•[/yellow] {w}")
        print_fn("")
        if not confirm_fn("Proceed despite warnings?"):
            print_fn("[dim]Cancelled.[/dim]")
            return 0
    else:
        print_fn("[green]PKGBUILD security scan passed[/green]")

    # 7. Show PKGBUILD
    print_fn("")
    if confirm_fn("View PKGBUILD before building?"):
        print_fn("\n[dim]─── PKGBUILD ───[/dim]")
        for line in pkgbuild_text.splitlines():
            print_fn(f"[dim]{line}[/dim]")
        print_fn("[dim]─── end PKGBUILD ───[/dim]\n")

    # 8. Final confirm
    if not confirm_fn(f"Build and install '{pkgname}' from AUR?"):
        print_fn("[dim]Cancelled.[/dim]")
        return 0

    # 9. Build and install
    print_fn(f"\n[dim]→ makepkg -si ...[/dim]\n")
    rc = builder.build(pkg_path)

    if rc == 0:
        print_fn(f"\n[green]✓ {pkgname} installed successfully.[/green]\n")
    else:
        pkgbuild_text2 = builder.read_pkgbuild(pkg_path)
        if "validpgpkeys" in pkgbuild_text2.lower() or rc == 1:
            keys = re.findall(r"[A-F0-9]{16,40}", pkgbuild_text2)
            if keys:
                print_fn("\n[yellow]Tip: This package requires PGP keys. Import them with:[/yellow]")
                for key in set(keys):
                    print_fn(f"  [cyan]gpg --recv-keys {key}[/cyan]")
                print_fn("  Then run centium aur again.\n")
        error_fn(f"makepkg failed with exit code {rc}")

    return rc
