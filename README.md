# centium

A minimal, preview-first package manager UX for Arch Linux — with AUR support.

![Python](https://img.shields.io/badge/python-3.11+-blue)
![Platform](https://img.shields.io/badge/platform-Arch%20Linux-blue)
![AUR](https://img.shields.io/aur/version/centium)

## What it does

centium never touches packages directly. Every command shows you exactly what is
about to happen, then hands off to pacman or builds from the AUR — your choice, your confirmation.

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

### search
```bash
centium search firefox
```
Clean sorted results instead of pacman's wall of text. Shows repo, version, and whether already installed.

### install
```bash
centium install firefox
```
Shows description, version, download size, installed size, and dependencies before asking you to confirm. Then hands off to pacman.

### aur
```bash
centium aur brave-bin
```
Full AUR install pipeline — no paru or yay required:
- Fetches package info from the AUR RPC
- Shows votes, popularity, maintainer, and dependencies
- Clones the AUR repo to ~/.cache/centium/aur/
- Scans the PKGBUILD for suspicious patterns before building
- Offers to show the full PKGBUILD for review
- Runs makepkg -si with your confirmation
- Detects PGP key issues and tells you exactly how to fix them

### risk
```bash
centium risk brave-bin
```
Scores an AUR package's trustworthiness before you install it — something yay and paru don't do.

Checks:
- Vote count — how many users have tested it
- Popularity — how widely it is installed
- Last updated — whether it is actively maintained
- Maintainer — whether the package is orphaned
- Out of date flag — whether it is behind upstream
- Package age — brand new packages carry more risk
- PKGBUILD security scan — detects suspicious patterns

Returns a score from 0-100 with a verdict: LOW / MEDIUM / HIGH / CRITICAL RISK.

### remove
```bash
centium remove firefox
```
Warns which installed packages depend on the target before removing. pacman handles the actual transaction.

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

### update
```bash
centium update
```
Shows exactly what would change before running pacman -Syu. Uses checkupdates from pacman-contrib for a safe lock-free preview. After updating, reports new .pacnew files and any newly failing services.

## Why centium

pacman is powerful but unforgiving. centium adds a preview layer — see what is going to happen, understand why, then decide.

The risk command fills a gap no other tool covers: a trust score for AUR packages before you install them. Given the 2026 AUR compromise incident, knowing whether a package is well-maintained and widely-used before running its PKGBUILD matters.

## Requirements

- Python 3.11+
- rich — installed automatically via AUR, or pip install --break-system-packages rich
- git and base-devel — for AUR installs
- pacman-contrib — optional, for safe update previews

## Also check out

- [hyprkit](https://github.com/Kolgrim33/hyprkit) — companion CLI for Hyprland (paru -S hyprkit-git)
- [pkgstory](https://github.com/Kolgrim33/pkgstory) — your Arch journey told through pacman.log (paru -S pkgstory)

## Roadmap

- Dependency resolution for AUR packages that depend on other AUR packages
- centium orphans — find and explain unused packages
- centium health — full system health report
- Config file for default behaviors
