# fish completion for centium

set -l commands search install remove update why aur risk suggest

complete -c centium -f
complete -c centium -n "not __fish_seen_subcommand_from $commands" -a search   -d "Search for packages"
complete -c centium -n "not __fish_seen_subcommand_from $commands" -a install  -d "Preview and install a package"
complete -c centium -n "not __fish_seen_subcommand_from $commands" -a remove   -d "Preview and remove a package"
complete -c centium -n "not __fish_seen_subcommand_from $commands" -a update   -d "Preview and apply system updates"
complete -c centium -n "not __fish_seen_subcommand_from $commands" -a why      -d "Explain why a package is installed"
complete -c centium -n "not __fish_seen_subcommand_from $commands" -a aur      -d "Install a package from the AUR"
complete -c centium -n "not __fish_seen_subcommand_from $commands" -a risk     -d "Assess the risk of an AUR package"
complete -c centium -n "not __fish_seen_subcommand_from $commands" -a suggest  -d "Suggest packages based on your setup"

# complete package names for install/remove/why
complete -c centium -n "__fish_seen_subcommand_from install remove why" -a "(pacman -Qq 2>/dev/null)"
