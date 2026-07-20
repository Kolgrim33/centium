import argparse
import sys

from rich.console import Console
from rich.text import Text
from rich.prompt import Confirm
from rich.rule import Rule

from centium import pacman_wrapper as pw
from centium import update_report as ur
from centium.aur import installer as aur_installer

console = Console(highlight=False)


# ── Output primitives ────────────────────────────────────────────────────────

def _header(text: str) -> None:
    console.print(f"\n[bold]{text}[/bold]")
    console.print(Rule(style="dim"))


def _field(label: str, value: str, value_style: str = "") -> None:
    label_text = f"  [dim]{label:<18}[/dim]"
    value_text = f"[{value_style}]{value}[/{value_style}]" if value_style else value
    console.print(f"{label_text}{value_text}")


def _warn(message: str) -> None:
    console.print(f"\n[yellow] {message}[/yellow]")


def _error(message: str) -> None:
    console.print(f"\n[red]  {message}[/red]")


def _ok(message: str) -> None:
    console.print(f"\n[green]  {message}[/green]")


def _cancelled() -> None:
    console.print("[dim]Cancelled.[/dim]")


# ── Transaction preview ───────────────────────────────────────────────────────

def _print_package_preview(info: dict) -> None:
    _header(f"Package: {info['name']}")
    _field("Description", info["description"])
    _field("Repository", info["repo"])
    _field("Version", info["version"])
    _field("Download size", info["download_size"])
    _field("Installed size", info["install_size"])
    deps = info["depends_on"] if info["depends_on"] and info["depends_on"] != "None" else "—"
    _field("Depends on", deps)
    console.print()


# ── Commands ─────────────────────────────────────────────────────────────────

def cmd_search(term: str) -> int:
    try:
        results = pw.search(term)
    except pw.PacmanError as e:
        _error(str(e))
        return 1

    if not results:
        console.print(f"No packages found matching [bold]{term}[/bold].")
        return 0

    def relevance(pkg):
        name = pkg["name"].lower()
        t = term.lower()
        if name == t:
            return 0
        if name.startswith(t):
            return 1
        return 2

    results = sorted(results, key=relevance)
    shown = results[:15]

    _header(f"Search: {term}  ({len(results)} results, showing {len(shown)})")

    for pkg in shown:
        installed_tag = " [green]installed[/green]" if pkg["installed"] else ""
        console.print(
            f"  [bold cyan]{pkg['name']}[/bold cyan]"
            f"  [dim]{pkg['repo']} / {pkg['version']}[/dim]"
            f"{installed_tag}"
        )
        if pkg["description"]:
            console.print(f"  [dim]{pkg['description']}[/dim]")
        console.print()

    if len(results) > 15:
        console.print(
            f"  [dim]… and {len(results) - 15} more."
            f" Use a more specific term to narrow results.[/dim]\n"
        )
    return 0


def cmd_install(pkg: str) -> int:
    try:
        info = pw.package_info(pkg)
    except pw.PacmanError as e:
        _error(str(e))
        return 1

    if info is None:
        _error(f"Package '{pkg}' not found.")
        console.print(f"  Try: [bold]centium search {pkg}[/bold]\n")
        return 1

    _print_package_preview(info)

    if not Confirm.ask("Install with pacman?", default=False):
        _cancelled()
        return 0

    console.print("[dim]→ pacman -S ...[/dim]\n")
    return pw.run_install(pkg)


def cmd_remove(pkg: str) -> int:
    dependents = pw.would_break_dependents(pkg)

    if dependents:
        _warn(f"Removing '{pkg}' may affect {len(dependents)} installed package(s) that depend on it:")
        for d in dependents[:10]:
            console.print(f"  [dim]•[/dim] {d}")
        if len(dependents) > 10:
            console.print(f"  [dim]… and {len(dependents) - 10} more.[/dim]")
        console.print(
            "\n  [dim]pacman will show you the full impact before anything is removed.[/dim]\n"
        )
    else:
        console.print(f"\nRemoving [bold]{pkg}[/bold] — no installed packages depend on it.\n")

    if not Confirm.ask("Continue with pacman?", default=False):
        _cancelled()
        return 0

    console.print("[dim]→ pacman -R ...[/dim]\n")
    return pw.run_remove(pkg)


def cmd_why(pkg: str) -> int:
    try:
        info = pw.package_why(pkg)
    except pw.PacmanError as e:
        _error(str(e))
        return 1

    if info is None:
        _error(f"Package '{pkg}' not found.")
        console.print(f"  Try: [bold]centium search {pkg}[/bold]\n")
        return 1

    _header(f"{info['name']} — why is this installed?")

    console.print(f"  [dim]{'description':<18}[/dim]{info['description']}")
    console.print(f"  [dim]{'version':<18}[/dim]{info['version']}")
    console.print(f"  [dim]{'size':<18}[/dim]{info['size']}")
    console.print()

    # Install reason
    if "explicitly" in info["install_reason"]:
        reason_str = "[green]explicitly installed by you[/green]"
    else:
        reason_str = "[yellow]installed as a dependency[/yellow]"
    console.print(f"  [dim]{'installed':<18}[/dim]{reason_str}")

    # Install date
    if info["days_ago"] is not None:
        console.print(
            f"  [dim]{'install date':<18}[/dim]{info['install_date']}  "
            f"[dim]({info['days_ago']} days ago)[/dim]"
        )
    else:
        console.print(f"  [dim]{'install date':<18}[/dim]{info['install_date']}")

    console.print()

    # Dependents
    if info["dependents"]:
        console.print(
            f"  [dim]{'required by':<18}[/dim]"
            f"[yellow]{len(info['dependents'])} package(s) depend on it:[/yellow]"
        )
        for d in info["dependents"][:5]:
            console.print(f"  {'':18}[dim]• {d}[/dim]")
        if len(info["dependents"]) > 5:
            console.print(f"  {'':18}[dim]… and {len(info['dependents']) - 5} more[/dim]")
        console.print()
        console.print(
            f"  [dim]{'verdict':<18}[/dim]"
            f"[red]removing this will affect other packages[/red]"
        )
    else:
        console.print(f"  [dim]{'required by':<18}[/dim]nothing depends on it")
        console.print()
        if "explicitly" in info["install_reason"]:
            console.print(
                f"  [dim]{'verdict':<18}[/dim]"
                f"[green]safe to remove if you no longer need it[/green]"
            )
        else:
            console.print(
                f"  [dim]{'verdict':<18}[/dim]"
                f"[yellow]orphan — no longer needed by anything[/yellow]"
            )

    console.print()

    # Running status
    if info["running"]:
        console.print(f"  [dim]{'currently':<18}[/dim][green]running[/green]")
    else:
        console.print(f"  [dim]{'currently':<18}[/dim][dim]not running[/dim]")

    console.print()
    return 0





def cmd_suggest() -> int:
    from centium import suggest as suggest_mod

    console.print("\n[dim]Scanning installed packages...[/dim]")
    installed = suggest_mod.get_installed()
    suggestions = suggest_mod.get_suggestions(installed)

    if not suggestions:
        _ok("No suggestions — your setup looks complete.")
        return 0

    _header(f"suggestions based on your installed packages")

    for group in suggestions:
        triggers = ", ".join(group["triggered_by"])
        console.print(f"\n  [dim]because you have {triggers}:[/dim]")
        for pkg, desc in group["missing"]:
            console.print(f"    {pkg:<30} [dim]{desc}[/dim]")

    console.print()
    console.print(f"  [dim]Install any of these with: centium aur <package> or centium install <package>[/dim]")
    console.print()
    return 0


def cmd_risk(pkg: str) -> int:
    from centium.aur import risk as risk_mod
    console.print(f"\n[dim]Assessing risk for '{pkg}'...[/dim]")

    report = risk_mod.assess(pkg)

    if report is None:
        _error(f"Package '{pkg}' not found in AUR.")
        return 1

    pkg_info = report.pkg
    _header(f"{pkg_info.get('Name', pkg)} — risk assessment")

    severity_label = {"ok": "ok  ", "warn": "warn", "info": "    "}

    for factor in report.factors:
        label = severity_label.get(factor.severity, "    ")
        console.print(f"  [dim]{label}[/dim]  {factor.message}")

    console.print()
    console.print(f"  [dim]score[/dim]  {report.score}/100  {report.level} RISK")
    console.print()

    if report.level == "LOW":
        console.print("  Safe to install.")
    elif report.level == "MEDIUM":
        console.print("  Proceed with caution — review the factors above.")
    elif report.level == "HIGH":
        console.print("  High risk — carefully review before installing.")
    else:
        console.print("  Critical risk — strongly advise against installing.")

    console.print()
    return 0


def cmd_aur_install(pkg: str) -> int:
    return aur_installer.install(
        pkg,
        confirm_fn=lambda msg: Confirm.ask(msg, default=False),
        print_fn=console.print,
        warn_fn=lambda msg: console.print(f"\n[yellow]⚠  {msg}[/yellow]"),
        error_fn=lambda msg: console.print(f"\n[red]✗  {msg}[/red]"),
    )


def cmd_update() -> int:
    console.print("\n[dim]Checking for available updates...[/dim]")
    updates = pw.update_preview()

    if not updates:
        _ok("System is up to date.")
        console.print(
            "  [dim](If you expected updates, ensure pacman-contrib is installed"
            " so centium can use checkupdates.)[/dim]\n"
        )
        if not Confirm.ask("Run pacman -Syu anyway?", default=False):
            _cancelled()
            return 0
        before = ur.snapshot()
        rc = pw.run_update()
        _print_post_update_summary(before, [])
        return rc

    _header(f"{len(updates)} update(s) available")

    for u in updates:
        old = Text(u["old_version"], style="red")
        new = Text(u["new_version"], style="green")
        line = Text()
        line.append(f"  {u['name']:<30}", style="bold")
        line.append_text(old)
        line.append(" → ")
        line.append_text(new)
        console.print(line)

    console.print()

    updated_names = [u["name"] for u in updates]
    if ur.kernel_was_updated(updated_names):
        _warn("This update includes a kernel package. A reboot will be required afterwards.")

    if not Confirm.ask("\nProceed with pacman -Syu?", default=False):
        _cancelled()
        return 0

    before = ur.snapshot()
    console.print("\n[dim]→ pacman -Syu ...[/dim]\n")
    rc = pw.run_update()
    _print_post_update_summary(before, updated_names)
    return rc


def _print_post_update_summary(before: dict, updated_packages: list[str]) -> None:
    after = ur.snapshot()
    diff = ur.diff_snapshots(before, after)

    _header("Update summary")
    console.print(f"  Packages updated: {len(updated_packages)}")

    if diff["new_pacnew_files"]:
        _warn(f"{len(diff['new_pacnew_files'])} new config file(s) need review:")
        for f in diff["new_pacnew_files"]:
            console.print(f"  [dim]•[/dim] {f}")
        console.print(
            "\n  [dim].pacnew files are upstream config defaults that couldn't be"
            " merged with your edits. Review with:[/dim] [bold]pacdiff[/bold]\n"
        )

    if diff["new_failed_services"]:
        _error(f"{len(diff['new_failed_services'])} service(s) newly failing after update:")
        for s in diff["new_failed_services"]:
            console.print(f"  [dim]•[/dim] {s}")
        console.print("  [dim]Inspect with:[/dim] [bold]systemctl status <service>[/bold]\n")

    if diff["resolved_failed_services"]:
        _ok(f"{len(diff['resolved_failed_services'])} previously-failing service(s) now healthy:")
        for s in diff["resolved_failed_services"]:
            console.print(f"  [dim]•[/dim] {s}")
        console.print()

    if not diff["new_pacnew_files"] and not diff["new_failed_services"]:
        _ok("No config conflicts or service failures detected.")
        console.print()


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="centium",
        description="A clear, minimal UX layer over pacman.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  centium search firefox\n"
            "  centium install firefox\n"
            "  centium remove firefox\n"
            "  centium update\n"
            "  centium why firefox\n\n"
            "Centium never installs or removes packages itself.\n"
            "It previews what will happen, then hands off to pacman."
        ),
    )
    sub = parser.add_subparsers(dest="command")

    s = sub.add_parser("search", help="Search for packages")
    s.add_argument("term")

    i = sub.add_parser("install", help="Preview and install a package")
    i.add_argument("package")

    r = sub.add_parser("remove", help="Preview and remove a package")
    r.add_argument("package")

    w = sub.add_parser("why", help="Explain why a package is installed")
    w.add_argument("package")

    sub.add_parser("suggest", help="Suggest packages that complement your setup")

    rk = sub.add_parser("risk", help="Assess the risk of installing an AUR package")
    rk.add_argument("package")

    a = sub.add_parser("aur", help="Install a package from the AUR")
    a.add_argument("package")

    sub.add_parser("update", help="Preview and apply system updates")

    args = parser.parse_args()

    if args.command == "search":
        return cmd_search(args.term)
    if args.command == "install":
        return cmd_install(args.package)
    if args.command == "remove":
        return cmd_remove(args.package)
    if args.command == "why":
        return cmd_why(args.package)
    if args.command == "suggest":
        return cmd_suggest()
    if args.command == "risk":
        return cmd_risk(args.package)
    if args.command == "aur":
        return cmd_aur_install(args.package)
    if args.command == "update":
        return cmd_update()

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
