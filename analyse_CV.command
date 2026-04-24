#!/bin/bash

# 1. Se placer dans le dossier où se trouve ce fichier .command
cd "$(dirname "$0")"


if ! osascript -e 'display dialog "Lancer le programme ?" buttons {"Non", "Oui"} default button "Oui" cancel button "Non" with title "Analyse CV" with icon note' > /dev/null 2>&1; then
    echo "Lancement annulé."
    osascript -e 'tell application "Terminal" to close front window' & exit 0
fi

# Fonction pour envoyer de belles notifications macOS silencieuses mais visuelles
notify() {
    osascript -e "display notification \"$1\" with title \"Analyse CV\" subtitle \"$2\""
}

echo "=== Démarrage du processus d'Analyse CV ==="

# 3. Lancer ton application Python
echo "🚀 Lancement de l'analyse..."
notify "Exécution en cours..." "uv run -m main"

# Lancer la commande uv
uv run -m main

# 4. Fin de l'exécution : Afficher une belle pop-up de succès
osascript -e 'display dialog "Analyse CV terminée avec succès, retrouver le fichier "classement_CV.json" conrtenant tout les CV triés. buttons {"Ok"} default button "Super !" giving up after 10 with title "Terminé" with icon note'

# 5. Fermer proprement la fenêtre du Terminal qui a lancé ce script
# On quitte d'abord le bash proprement
osascript -e 'tell application "Terminal" to close front window' & exit 0
