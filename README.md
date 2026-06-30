# centium

A friendlier UX wrapper around pacman. Centium never touches packages
directly — every command previews what's about to happen, then hands off
to real, interactive pacman for the actual transaction.

## Install (dev mode)

```bash
pip install --break-system-packages -e .
```

## Usage

```bash
centium search firefox     # clean table instead of pacman's wall of text
centium install firefox    # shows size/deps/description before confirming, then runs real pacman -S
centium remove firefox     # warns if other installed packages depend on it
centium update             # shows what would update before running pacman -Syu
```

`centium update` uses `checkupdates` (from pacman-contrib) if available for
a safe, lock-free preview. Install it with: `sudo pacman -S pacman-contrib`

## Roadmap

- AUR search/install passthrough (still no own build logic — delegate to
  an existing helper if installed)
- Post-install summary / rollback hints
- Config file for default behaviors (always show deps, skip preview, etc.)
