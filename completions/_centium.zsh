#compdef centium
# zsh completion for centium

_centium() {
    local -a commands
    commands=(
        "search:Search for packages"
        "install:Preview and install a package"
        "remove:Preview and remove a package"
        "update:Preview and apply system updates"
        "why:Explain why a package is installed"
        "aur:Install a package from the AUR"
        "risk:Assess the risk of an AUR package"
        "suggest:Suggest packages based on your setup"
    )

    local -a installed_pkgs
    installed_pkgs=(${(f)"$(pacman -Qq 2>/dev/null)"})

    _arguments -C         "1: :->command"         "*: :->args"

    case $state in
        command)
            _describe "command" commands
            ;;
        args)
            case $words[2] in
                install|remove|why)
                    _describe "package" installed_pkgs
                    ;;
            esac
            ;;
    esac
}

_centium
