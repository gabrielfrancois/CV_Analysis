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

# Vérifier si Homebrew est installé
if ! command -v brew &> /dev/null; then
    notify "Erreur critique" "Homebrew n'est pas installé."
    echo "❌ Erreur : Homebrew est introuvable. Installez-le d'abord (https://brew.sh/)."
    exit 1
fi

# Vérifier si Ollama est installé
if ! command -v ollama &> /dev/null; then
    echo "⚠️ Ollama n'est pas installé. Installation via Homebrew en cours..."
    notify "Installation" "Téléchargement d'Ollama..."
    brew install ollama
fi

echo "✅ Démarrage du serveur Ollama..."
notify "Info" "Lancement d'Ollama en arrière-plan..."
# On lance ollama serve en tâche de fond (&) pour ne pas bloquer la suite du script
ollama serve > /dev/null 2>&1 &
sleep 3

# Lancer la commande uv
uv run -m main

# 4. Fin de l'exécution : Afficher une belle pop-up de succès
osascript -e 'display dialog "Analyse CV terminée avec succès, retrouver le fichier "classement_CV.json" conrtenant tout les CV triés. buttons {"Ok"} default button "Super !" giving up after 10 with title "Terminé" with icon note'

# 5. Fermer proprement la fenêtre du Terminal qui a lancé ce script
# On quitte d'abord le bash proprement
osascript -e 'tell application "Terminal" to close front window' & exit 0
