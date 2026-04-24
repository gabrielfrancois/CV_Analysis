# Guide d'utilisation : Analyseur de CV Local

Ce programme permet d'évaluer automatiquement une liste de CV au format PDF en utilisant l'intelligence artificielle installée sur ce Mac. Le processus est entièrement privé : aucun document ne sort de cet ordinateur.

---

## 1. Avant de commencer
Pour que l'analyse puisse fonctionner, l'application **LM Studio** doit être prête :
1. Ouvrez **LM Studio**.
2. Vérifiez que le modèle est bien chargé (barre de sélection en haut).
3. Allez dans l'onglet **Local Server** (icône `<->` à gauche) et cliquez sur le bouton vert **Start Server**.

---

## 2. Utilisation simple
1. **Déposer les CV** : Copiez vos fichiers PDF dans le dossier nommé `data`.
2. **Lancer l'analyse** : Double-cliquez sur le fichier `Lancer_Analyse.command` (celui avec l'icône de baguette magique). Une fenêtre de terminal s'ouvrira pour montrer l'avancement.
3. **Consulter les notes** : Une fois terminé, le fichier `classement_cv.json` s'ouvrira automatiquement dans **TextEdit** avec la liste des candidats classés du meilleur au moins bon.

---

## 3. Personnaliser les critères de sélection
Si vous changez de poste ou de critères, vous pouvez modifier les instructions données à l'IA :

1. Faites un clic droit sur le fichier `main.py` et choisissez **Ouvrir avec > TextEdit**.
2. Cherchez la section qui commence par : `system_prompt = """`.
3. Vous pouvez réécrire la description du poste et ce que vous recherchez.
4. **Attention** : Ne modifiez que le texte situé **avant** la ligne `RÈGLES STRICTES`. 
   *Conservez impérativement tout ce qui suit cette ligne pour que le programme continue de fonctionner normalement.*
5. Enregistrez le fichier (`CMD + S`) et fermez-le.

---

## 4. Remarques importantes
* **Format des fichiers** : Seuls les fichiers PDF sont analysés. Si un CV est une image scannée (sans texte sélectionnable à la souris), l'IA ne pourra pas lire le contenu et mettra une note de 0.
* **Télétravail** : Le programme n'a pas besoin d'internet pour fonctionner.
