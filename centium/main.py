import argparse
import sys

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm

from centium import pacman_wrapper as pw

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
        return pw.run_update()

    table = Table(title=f"{len(updates)} update(s) available")
    table.add_column("Package")
    table.add_column("Current")
    table.add_column("New")
    for u in updates:
        table.add_row(u["name"], u["old_version"], u["new_version"])
    console.print(table)

    if not Confirm.ask("Proceed with update?"):
        console.print("[yellow]Cancelled.[/yellow]")
        return 0

    console.print("[dim]Handing off to pacman...[/dim]\n")
    return pw.run_update()


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
