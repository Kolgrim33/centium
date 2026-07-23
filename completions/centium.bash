# bash completion for centium
_centium() {
    local cur prev words cword
    _init_completion || return

    local commands="search install remove update why aur risk suggest"

    case "$prev" in
        centium)
            COMPREPLY=($(compgen -W "$commands" -- "$cur"))
            return 0
            ;;
        install|remove|why|info)
            # complete with installed package names
            COMPREPLY=($(compgen -W "$(pacman -Qq 2>/dev/null)" -- "$cur"))
            return 0
            ;;
        search|aur|risk)
            # no completion for these — they take arbitrary terms
            return 0
            ;;
        suggest|update)
            return 0
            ;;
    esac

    COMPREPLY=($(compgen -W "$commands" -- "$cur"))
}

complete -F _centium centium
