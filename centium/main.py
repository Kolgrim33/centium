import argparse
import sys

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm

from centium import pacman_wrapper as pw
from centium import update_report as ur

console = Console()


def cmd_search(term: str) -> int:
    try:
        results = pw.search(term)
    except pw.PacmanError as e:
        console.print(f"[red]Error:[/red] {e}")
        return 1

    if not results:
        console.print(f"[yellow]No packages found matching '{term}'.[/yellow]")
        return 0

    # Exact/close name matches first, so the thing you're actually
    # looking for doesn't get buried under language packs and unrelated
    # partial matches.
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
    console.print(f"[bold]Search results for '{term}'[/bold] ({len(results)} total, showing top {len(shown)})\n")

    for pkg in shown:
        installed = " [green]✓ installed[/green]" if pkg["installed"] else ""
        console.print(f"[bold cyan]{pkg['name']}[/bold cyan] [dim]{pkg['repo']}/{pkg['version']}[/dim]{installed}")
        console.print(f"  {pkg['description']}\n")

    if len(results) > 15:
        console.print(f"[dim]...and {len(results) - 15} more (mostly language packs/extras). Use a more specific search term to narrow this down.[/dim]")
    return 0


def cmd_install(pkg: str) -> int:
    try:
        info = pw.package_info(pkg)
    except pw.PacmanError as e:
        console.print(f"[red]Error:[/red] {e}")
        return 1

    if info is None:
        console.print(f"[red]Package '{pkg}' not found.[/red] Try `centium search {pkg}` to find the right name.")
        return 1

    body = (
        f"[bold]{info['name']}[/bold] ({info['repo']})\n"
        f"{info['description']}\n\n"
        f"Version: {info['version']}\n"
        f"Download size: {info['download_size']}\n"
        f"Installed size: {info['install_size']}\n"
        f"Depends on: {info['depends_on']}"
    )
    console.print(Panel(body, title="About to install", border_style="cyan"))

    if not Confirm.ask("Proceed?"):
        console.print("[yellow]Cancelled.[/yellow]")
        return 0

    console.print("[dim]Handing off to pacman...[/dim]\n")
    return pw.run_install(pkg)


def cmd_remove(pkg: str) -> int:
    dependents = pw.would_break_dependents(pkg)
    if dependents:
        console.print(f"[yellow]Warning:[/yellow] {len(dependents)} installed package(s) depend on '{pkg}':")
        for d in dependents[:10]:
            console.print(f"  - {d}")
        if not Confirm.ask("Removing it may break these. Continue anyway?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return 0
    else:
        if not Confirm.ask(f"Remove '{pkg}'?"):
            console.print("[yellow]Cancelled.[/yellow]")
            return 0

    console.print("[dim]Handing off to pacman...[/dim]\n")
    return pw.run_remove(pkg)


def cmd_update() -> int:
    console.print("[cyan]Checking for updates...[/cyan]\n")
    updates = pw.update_preview()

    if not updates:
        console.print("[green]System is up to date (or `checkupdates` is unavailable — pacman-contrib not installed).[/green]")
        if not Confirm.ask("Run `pacman -Syu` anyway?"):
            return 0
        before = ur.snapshot()
        rc = pw.run_update()
        _print_post_update_summary(before, [])
        return rc

    table = Table(title=f"{len(updates)} update(s) available")
    table.add_column("Package")
    table.add_column("Current")
    table.add_column("New")
    for u in updates:
        table.add_row(u["name"], u["old_version"], u["new_version"])
    console.print(table)

    if ur.kernel_was_updated([u["name"] for u in updates]):
        console.print("[yellow]Note:[/yellow] This update includes a new kernel — a reboot will be needed for it to take effect.\n")

    if not Confirm.ask("Proceed with update?"):
        console.print("[yellow]Cancelled.[/yellow]")
        return 0

    before = ur.snapshot()
    console.print("[dim]Handing off to pacman...[/dim]\n")
    rc = pw.run_update()
    _print_post_update_summary(before, [u["name"] for u in updates])
    return rc


def _print_post_update_summary(before: dict, updated_packages: list[str]) -> None:
    after = ur.snapshot()
    diff = ur.diff_snapshots(before, after)

    console.print("\n[bold]Update summary[/bold]")
    console.print(f"  Packages updated: {len(updated_packages)}")

    if diff["new_pacnew_files"]:
        console.print(f"\n[yellow]⚠ {len(diff['new_pacnew_files'])} new .pacnew/.pacsave file(s) appeared:[/yellow]")
        for f in diff["new_pacnew_files"]:
            console.print(f"    {f}")
        console.print("  [dim]These are new upstream config defaults that weren't auto-merged with your edits. Review and merge manually, e.g. with: pacdiff[/dim]")

    if diff["new_failed_services"]:
        console.print(f"\n[red]✗ {len(diff['new_failed_services'])} service(s) failed after the update:[/red]")
        for s in diff["new_failed_services"]:
            console.print(f"    {s}")
        console.print("  [dim]Check with: systemctl status <service>[/dim]")

    if diff["resolved_failed_services"]:
        console.print(f"\n[green]✓ {len(diff['resolved_failed_services'])} previously-failed service(s) now OK:[/green]")
        for s in diff["resolved_failed_services"]:
            console.print(f"    {s}")

    if not diff["new_pacnew_files"] and not diff["new_failed_services"]:
        console.print("\n[green]No new config conflicts or service failures detected.[/green]")


def main() -> int:
    parser = argparse.ArgumentParser(prog="centium", description="A friendlier UX wrapper around pacman.")
    sub = parser.add_subparsers(dest="command")

    search_parser = sub.add_parser("search", help="Search for a package")
    search_parser.add_argument("term")

    install_parser = sub.add_parser("install", help="Install a package with a preview")
    install_parser.add_argument("package")

    remove_parser = sub.add_parser("remove", help="Remove a package with dependent warnings")
    remove_parser.add_argument("package")

    sub.add_parser("update", help="Update the system with a preview")

    args = parser.parse_args()

    if args.command == "search":
        return cmd_search(args.term)
    if args.command == "install":
        return cmd_install(args.package)
    if args.command == "remove":
        return cmd_remove(args.package)
    if args.command == "update":
        return cmd_update()

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
