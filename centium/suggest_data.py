"""
centium suggest — curated package pairing dataset.
Each entry: if user has ANY of "triggers" installed,
suggest packages in "suggests" they don't already have.
"""

PAIRINGS = [
    # ── Hyprland ecosystem ─────────────────────────────────────────────
    {
        "triggers": ["hyprland"],
        "suggests": [
            ("hypridle",    "idle daemon — auto-lock and screen-off"),
            ("hyprlock",    "screen locker for Hyprland"),
            ("hyprpaper",   "wallpaper manager for Hyprland"),
            ("hyprshot",    "screenshot tool built for Hyprland"),
            ("hyprpicker",  "color picker for Hyprland"),
        ],
    },
    {
        "triggers": ["hyprland"],
        "suggests": [
            ("waybar",      "status bar — most popular Hyprland bar"),
            ("wofi",        "app launcher for Wayland"),
            ("rofi-wayland","rofi with Wayland support"),
            ("dunst",       "lightweight notification daemon"),
            ("mako",        "Wayland native notification daemon"),
        ],
    },
    {
        "triggers": ["hyprland", "sway", "river"],
        "suggests": [
            ("wl-clipboard", "clipboard support for Wayland (wl-copy/wl-paste)"),
            ("grim",         "screenshot tool for Wayland"),
            ("slurp",        "select screen region — pairs with grim"),
            ("swappy",       "screenshot annotation tool"),
            ("cliphist",     "clipboard history manager for Wayland"),
        ],
    },

    # ── Terminal / shell ───────────────────────────────────────────────
    {
        "triggers": ["kitty", "alacritty", "foot", "wezterm", "ghostty"],
        "suggests": [
            ("starship",    "fast, minimal shell prompt"),
            ("zsh",         "shell with better completion than bash"),
            ("fish",        "user-friendly shell with autosuggestions"),
            ("tmux",        "terminal multiplexer — split panes, sessions"),
            ("zellij",      "modern terminal multiplexer"),
        ],
    },
    {
        "triggers": ["zsh"],
        "suggests": [
            ("zsh-autosuggestions",  "fish-like autosuggestions for zsh"),
            ("zsh-syntax-highlighting", "syntax highlighting for zsh"),
            ("starship",             "fast cross-shell prompt"),
        ],
    },

    # ── Neovim ecosystem ───────────────────────────────────────────────
    {
        "triggers": ["neovim"],
        "suggests": [
            ("ripgrep",     "fast grep — used by telescope.nvim"),
            ("fd",          "fast find — used by telescope.nvim"),
            ("lazygit",     "terminal git UI — integrates with neovim"),
            ("tree-sitter", "parser generator — powers nvim-treesitter"),
            ("nodejs",      "required by many LSP servers"),
        ],
    },

    # ── Git / development ──────────────────────────────────────────────
    {
        "triggers": ["git"],
        "suggests": [
            ("lazygit",     "terminal UI for git"),
            ("git-delta",   "beautiful git diffs in the terminal"),
            ("gh",          "GitHub CLI — PRs, issues from terminal"),
            ("tig",         "text-mode git interface"),
        ],
    },
    {
        "triggers": ["docker"],
        "suggests": [
            ("lazydocker",  "terminal dashboard for docker"),
            ("dive",        "explore docker image layers"),
            ("docker-compose", "multi-container Docker apps"),
            ("ctop",        "top-like interface for containers"),
        ],
    },

    # ── System monitoring ──────────────────────────────────────────────
    {
        "triggers": ["htop"],
        "suggests": [
            ("btop",        "modern resource monitor with graphs"),
            ("bpytop",      "Python-based resource monitor"),
            ("nvtop",       "GPU process monitor"),
        ],
    },
    {
        "triggers": ["btop", "bpytop"],
        "suggests": [
            ("nvtop",       "GPU process monitor — pairs with btop"),
            ("bandwhich",   "network utilization by process"),
            ("dust",        "more intuitive du — disk usage"),
        ],
    },

    # ── File management ────────────────────────────────────────────────
    {
        "triggers": ["ranger", "lf", "nnn", "yazi"],
        "suggests": [
            ("bat",         "cat with syntax highlighting"),
            ("eza",         "modern ls replacement"),
            ("fd",          "fast find alternative"),
            ("fzf",         "fuzzy finder — pairs with any file manager"),
            ("ripgrep",     "fast grep"),
        ],
    },

    # ── Multimedia ─────────────────────────────────────────────────────
    {
        "triggers": ["mpv"],
        "suggests": [
            ("yt-dlp",      "download videos — integrates with mpv"),
            ("ffmpeg",      "video/audio processing"),
        ],
    },
    {
        "triggers": ["pipewire"],
        "suggests": [
            ("pipewire-pulse",  "PulseAudio compatibility layer"),
            ("wireplumber",     "session manager for PipeWire"),
            ("pavucontrol",     "GUI volume control for PipeWire/Pulse"),
            ("easyeffects",     "audio effects for PipeWire"),
        ],
    },

    # ── Arch-specific ──────────────────────────────────────────────────
    {
        "triggers": ["pacman"],
        "suggests": [
            ("pacman-contrib",  "extra pacman tools: checkupdates, pacdiff"),
            ("pkgstory",        "visualize your pacman.log history"),
            ("centium",         "preview-first pacman UX with AUR support"),
            ("paru",            "AUR helper"),
        ],
    },
    {
        "triggers": ["hyprland", "sway"],
        "suggests": [
            ("hyprkit",         "companion CLI for Hyprland — lint, doctor, config"),
            ("xdg-desktop-portal-hyprland", "screen sharing on Wayland"),
        ],
    },

    # ── Fonts ──────────────────────────────────────────────────────────
    {
        "triggers": ["waybar", "kitty", "alacritty", "foot", "neovim"],
        "suggests": [
            ("ttf-jetbrains-mono-nerd", "JetBrains Mono with Nerd Font icons"),
            ("ttf-nerd-fonts-symbols",  "Nerd Font symbols only"),
            ("noto-fonts-emoji",        "emoji support"),
        ],
    },
]
