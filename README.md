# centium

A minimal, preview-first package manager UX for Arch Linux — with AUR support.

![Python](https://img.shields.io/badge/python-3.11+-blue)
![Platform](https://img.shields.io/badge/platform-Arch%20Linux-blue)
![AUR](https://img.shields.io/aur/version/centium)

## What it does

centium never touches packages directly. Every command shows you exactly what is
about to happen, then hands off to pacman or builds from the AUR.

## Install

**From the AUR (recommended):**
```bash
paru -S centium
```

**From source:**
```bash
git clone https://github.com/Kolgrim33/centium.git
cd centium
pip install --break-system-packages -e .
```

## Commands

### suggest
```bash
centium suggest
```
Scans your installed packages and surfaces complementary tools you might be missing.
No other AUR helper or pacman wrapper does proactive discovery based on what you already have.
because you have hyprland:
hypridle                       idle daemon — auto-lock and screen-off
hyprlock                       screen locker for Hyprland
because you have neovim:
ripgrep                        fast grep — used by telescope.nvim
lazygit                        terminal git UI — integrates with neovim
because you have docker:
lazydocker                     terminal dashboard for docker
dive                           explore docker image layers

### risk
```bash
centium risk brave-bin
```
Scores an AUR package trustworthiness before you install it. Checks votes, popularity,
maintainer status, out-of-date flag, package age, and scans the PKGBUILD for suspicious
patterns. Returns a score from 0-100 with a verdict: LOW / MEDIUM / HIGH / CRITICAL RISK.

Especially relevant given the 2026 AUR compromise — know what you are installing before
you run it.

### aur
```bash
centium aur brave-bin
```
Full AUR install pipeline with recursive dependency resolution — no paru or yay required.

- Fetches package info from the AUR RPC
- Automatically detects and installs AUR dependencies before the main package
- Clones the AUR repo to ~/.cache/centium/aur/
- Scans the PKGBUILD for suspicious patterns
- Offers to show the full PKGBUILD for review
- Runs makepkg -si with your confirmation
- Detects PGP key issues and tells you exactly how to fix them

### why
```bash
centium why firefox
```
Explains why a package is installed in plain English:
- Whether you installed it explicitly or it came in as a dependency
- When it was installed and how many days ago
- What depends on it or if it is an orphan
- Whether it is currently running
- A verdict: safe to remove or will break other packages

### install
```bash
centium install firefox
```
Shows description, version, download size, and dependencies before confirming.
Hands off to pacman.

### remove
```bash
centium remove firefox
```
Warns which installed packages depend on the target before removing.

### update
```bash
centium update
```
Shows exactly what would change before running pacman -Syu. After updating, reports
new .pacnew files and any newly failing services.

### search
```bash
centium search firefox
```
Clean sorted results instead of pacman wall of text. Shows repo, version, and
whether already installed.

## What makes centium different

| Feature | centium | paru | yay |
|---|---|---|---|
| Preview before every action | yes | partial | partial |
| AUR dep resolution | recursive | yes | yes |
| Risk scoring before install | yes | no | no |
| Proactive package suggestions | yes | no | no |
| Plain English why explanation | yes | no | no |
| Post-update service report | yes | no | no |

## Requirements

- Python 3.11+
- rich — installed automatically via AUR, or pip install --break-system-packages rich
- git and base-devel — for AUR installs
- pacman-contrib — optional, for safe update previews

## Also check out

- [hyprkit](https://github.com/Kolgrim33/hyprkit) — companion CLI for Hyprland (paru -S hyprkit-git)
- [pkgstory](https://github.com/Kolgrim33/pkgstory) — your Arch journey told through pacman.log (paru -S pkgstory)

## Roadmap

- centium orphans — find and explain unused packages
- centium health — full system health report
- Expand suggest pairing dataset with community contributions
