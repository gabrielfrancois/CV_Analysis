#!/bin/bash

# 1. Se placer dans le dossier où se trouve ce fichier .command
cd "$(dirname "$0")"

PORT=1234

# Fonction pour envoyer de belles notifications macOS silencieuses mais visuelles
notify() {
    osascript -e "display notification \"$1\" with title \"Analyse CV\" subtitle \"$2\""
}

# Fonction pour vérifier si le port de l'API est ouvert
check_port() {
    nc -z localhost $PORT > /dev/null 2>&1
    return $?
}

echo "=== Démarrage du processus d'Analyse CV ==="

# 2. Vérifier si LM Studio est lancé (pgrep cherche le processus)
if pgrep -fi "LM Studio" > /dev/null; then
    echo "✅ LM Studio est déjà ouvert."
    
    if check_port; then
        echo "✅ Le port $PORT (API) est déjà ouvert."
    else
        echo "⚠️ L'API n'est pas active. Activation en cours..."
        notify "Activation du serveur local..." "Lancement de l'API sur le port $PORT"
        # Utilise la commande lms intégrée à LM Studio pour lancer le serveur en arrière-plan
        lms server start &
        sleep 5
    fi
else
    echo "❌ LM Studio n'est pas ouvert."
    notify "Lancement de LM Studio..." "Veuillez patienter 15 secondes."
    
    # Lancer l'application LM Studio
    open -a "LM Studio"
    
    # Attendre 15 secondes comme demandé
    sleep 15
    
    # Vérifier si le port s'est activé tout seul, sinon l'activer
    if ! check_port; then
         echo "Activation de l'API..."
         lms server start &
         sleep 5
    fi
fi

# 3. Lancer ton application Python
echo "🚀 Lancement de l'analyse..."
notify "Exécution en cours..." "uv run -m main"

# Lancer la commande uv
uv run -m main

# 4. Fin de l'exécution : Afficher une belle pop-up de succès
osascript -e 'display dialog "Analyse CV terminée avec succès !" buttons {"Super !"} default button "Super !" giving up after 10 with title "Terminé" with icon note'

# 5. Fermer proprement la fenêtre du Terminal qui a lancé ce script
# On quitte d'abord le bash proprement
osascript -e 'tell application "Terminal" to close front window' & exit 0
