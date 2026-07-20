# centium

A minimal, preview-first package manager UX for Arch Linux — with AUR support.

![Python](https://img.shields.io/badge/python-3.11+-blue)
![Platform](https://img.shields.io/badge/platform-Arch%20Linux-blue)
![AUR](https://img.shields.io/aur/version/centium)

## What it does
<img width="1879" height="967" alt="centium" src="https://github.com/user-attachments/assets/4d7f6010-428c-440b-8b94-ec76b605a890" />

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
No other AUR helper or pacman wrapper does this , discovery based on what you already have.

Example output:
because you have hyprland:
hypridle                       idle daemon — auto-lock and screen-off
hyprlock                       screen locker for Hyprland
hyprpaper                      wallpaper manager for Hyprland
because you have neovim:
ripgrep                        fast grep — used by telescope.nvim
lazygit                        terminal git UI — integrates with neovim
because you have docker:
lazydocker                     terminal dashboard for docker
dive                           explore docker image layers

### risk
<img width="1411" height="703" alt="centium1" src="https://github.com/user-attachments/assets/d17ef9f1-b26c-47d8-afc2-852a364d0b26" />

```bash
centium risk brave-bin
```
Scores an AUR package trustworthiness before you install it. Checks votes, popularity,
last updated, maintainer status, out-of-date flag, package age, and PKGBUILD security scan.
Returns a score from 0-100 with a verdict: LOW / MEDIUM / HIGH / CRITICAL RISK.

### aur

```bash
centium aur brave-bin
```
Full AUR install pipeline — no paru or yay required. Clones the repo, scans the PKGBUILD
for suspicious patterns, offers review, runs makepkg, detects PGP issues.

### why
<img width="1557" height="628" alt="centium4" src="https://github.com/user-attachments/assets/7986a470-ba52-4940-915a-db9468a90ac6" />

```bash
centium why firefox
```
Explains why a package is installed in plain English — when it was installed, what depends
on it, whether it is an orphan, whether it is currently running, and a verdict on safety to remove.

### install
```bash
centium install firefox
```
Shows description, version, download size, and dependencies before confirming. Hands off to pacman.

### remove
```bash
centium remove firefox
```
Warns which installed packages depend on the target before removing.

### update
```bash
centium update
```
Shows exactly what would change before running pacman -Syu. Reports new .pacnew files
and newly failing services after the update completes.

### search
```bash
centium search firefox
```
Clean sorted results instead of pacman wall of text.

## Why centium

pacman is powerful but unforgiving. centium adds a preview layer and three features
no other tool has:

- suggest — proactive discovery based on your installed packages
- risk — trust score for AUR packages before you run their PKGBUILD
- why — plain English explanation of why a package exists on your system

## Requirements

- Python 3.11+
- rich — installed automatically via AUR, or pip install --break-system-packages rich
- git and base-devel — for AUR installs
- pacman-contrib — optional, for safe update previews

## Also check out

- [hyprkit](https://github.com/Kolgrim33/hyprkit) :companion CLI for Hyprland (centium aur hyprkit-git)
- [pkgstory](https://github.com/Kolgrim33/pkgstory) : your Arch journey told through pacman.log (centium aur pkgstory)

## Roadmap

- Dependency resolution for AUR packages that depend on other AUR packages
- centium orphans — find and explain unused packages
- centium health — full system health report
- Community contributions to the suggest pairing dataset
