import PyPDF2
from openai import OpenAI
import os
import json
import re
import subprocess
from prints import *

def extraire_texte_pdf(chemin_pdf):
    """Extrait le texte brut d'un fichier PDF."""
    texte_complet = ""
    try:
        with open(chemin_pdf, 'rb') as fichier:
            lecteur = PyPDF2.PdfReader(fichier)
            for page in lecteur.pages:
                texte_page = page.extract_text()
                if texte_page:
                    texte_complet += texte_page + "\n"
        return texte_complet
    except Exception as e:
        print(red(f"❌ Impossible de lire {chemin_pdf}: {e}"))
        return ""

def evaluer_cv(client, cv_text):
    """Envoie le texte à l'IA et récupère une note numérique."""
    system_prompt = """
    Tu es un recruteur expert, froid et extrêmement exigeant pour SROPL'Form.
    CONTEXTE : SROPL'Form est un organisme de formation professionnel continu dédié spécifiquement aux orthophonistes et aux professionnels de santé.
    L'activité consiste à organiser des sessions de formation technique, gérer des financements publics (type DPC ou FIF-PL), les inscriptions administratives des stagiaires
    et assurer un suivi administratif sans faille pour des praticiens exigeants. Le poste contient un volet de promotion communication pour réaliser les supports de promotion des formations.
    C'est aussi une profession qui nécessite de bonnes capacités de communication.
    Ton objectif est de filtrer sans pitié les CV pour ne garder que l'excellence.

    ### CRITÈRES DE NOTATION PRIORITAIRES (par ordre d'importance) :
    1. DIPLÔME (Éliminatoire) : Bac+2 minimum en administration. Si < Bac+2, la note ne peut pas dépasser 5/100.
    2. EXPERIENCE PROFESSIONNELLE : au moins 5 ans d'expérience professionnelle dnas le monde de la formation sur un poste de secrétaire ou d'assistante ou d'ingénieur ((OPCO, Qualiopi, gestion de stages). La note est au maximum de 10/100.
    3. AUTONOMIE (Télétravail) : Capacité à travailler seul (100% télétravail). Autonomie dans l'exécution de ses missions (aller chercher dans la typologie des missions et non seulement dans les soft skills. La note est au maximum de 25/100.
    4. RIGUEUR : habitude à effectuer du traitement de dossier, du suivi d'inscription, une gestion de l'interface informatique dédiée. La note est au maximum de 25/100.
    5. Sens du relationnel (contacts téléphonique et par mail). la note est au maximum de 15/100.
    6. Très bon niveau en français écrit et oral. La note ets au maximum de 15/100.
    7. TECHNIQUE : Maîtrise prouvée (pas juste citée) du Pack Office et de logiciels de gestion (CRM, ERP). La note est au maximum de 5/100.

    CRITERE ELIMINATOIRE : **tu mettras 0 à tout profil non domicilé dans les pays de la Loire**

    ### TON ATTITUDE DE RECRUTEUR :
    - NE SOIS PAS GENTIL. Ne cherche pas à encourager le candidat.
    - DÉTECTION DE "FLUFF" : Ignore les adjectifs bateaux sans preuves (ex: "dynamique", "motivé", "sens du relationnel"). Si ce n'est pas lié à une mission précise avec un résultat, cela vaut 0.
    - SÉVÉRITÉ : Un CV qui n'a pas travaillé dans la formation ne peut pas avoir plus de 60/20, même s'il est excellent ailleurs.
    ### RÈGLES STRICTES :
    1. Réponds UNIQUEMENT avec un nombre entier ou décimal sur 100.
    2. Ne donne aucune explication.
    Exemple de réponse attendue : 50,5

    RAPPEL FINAL : Tu es un recruteur sévère. Analyse les preuves, ignore le superflu. Note sur 100 uniquement :

    """

    user_prompt = f"Contenu du CV :\n{cv_text}\n\nNote sur 100 :"

    try:
        response = client.chat.completions.create(
            model="johnlockejrr",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            max_tokens=10
        )

        # Nettoyage de la réponse pour ne garder que le chiffre
        contenu = response.choices[0].message.content.strip()
        # On utilise une expression régulière pour trouver le premier nombre dans la réponse
        match = re.search(r"(\d+[\.,]?\d*)", contenu)
        if match:
            return float(match.group(1).replace(',', '.'))
        return 0.0
    except Exception as e:
        print(f"❌ Erreur API : {e}")
        return 0.0

def main():
    # Configuration
    client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
    dossier_data = "data"
    resultats = []

    if not os.path.exists(dossier_data):
        print(f"Erreur : Le dossier '{dossier_data}' n'existe pas.")
        return

    fichiers_pdf = [f for f in os.listdir(dossier_data) if f.lower().endswith('.pdf')]

    if not fichiers_pdf:
        print("Aucun fichier PDF trouvé dans le dossier data.")
        return

    print(f"Début de l'analyse de {len(fichiers_pdf)} CV...")

    for nom_fichier in fichiers_pdf:
        chemin_complet = os.path.join(dossier_data, nom_fichier)
        print(f"Analyse de : {nom_fichier}...")

        texte = extraire_texte_pdf(chemin_complet)
        if texte:
            note = evaluer_cv(client, texte)
            resultats.append({
                "nom_fichier": nom_fichier,
                "chemin": chemin_complet,
                "note": note
            })
            print(f"-> Note : {note}/100")

    # (les meilleurs en premier)
    resultats_tries = sorted(resultats, key=lambda x: x['note'], reverse=True)

    # Sauvegarde en JSON
    with open("classement_cv.json", "w", encoding="utf-8") as f:
        json.dump(resultats_tries, f, indent=4, ensure_ascii=False)

    print("\n✅ Analyse terminée !")
    print(f"Le classement a été sauvegardé dans 'classement_cv.json'.")

    with open("classement_cv.json", "w", encoding="utf-8") as f:
        json.dump(resultats_tries, f, indent=4, ensure_ascii=False)

    print("\n✅ Analyse terminée !")
    print(f"Le classement a été sauvegardé dans 'classement_cv.json'.")

    # Commande magique pour ouvrir le fichier automatiquement sur Mac
    try:
        subprocess.run(["open", "-a", "TextEdit", "classement_cv.json"])
    except Exception as e:
        print(f"Erreur lors de l'ouverture du fichier : {e}")

if __name__ == "__main__":
    main()
