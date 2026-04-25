import json
import os
import re
import subprocess
import platform

import ollama
import PyPDF2

from prints import *

from config import EVALUATION_CRITERION, MODEL_ID 

def extraire_texte_pdf(chemin_pdf):
    """
    Extracts raw text from a PDF file.
        Args:
            chemin_pdf (str): Path to the PDF file.
        Returns:
            str: Extracted text content.
    """

    texte_complet = ""
    try:
        with open(chemin_pdf, "rb") as fichier:
            lecteur = PyPDF2.PdfReader(fichier)
            for page in lecteur.pages:
                texte_page = page.extract_text()
                if texte_page:
                    texte_complet += texte_page + "\n"
        return texte_complet
    except Exception as e:
        print(red(f"❌ Impossible de lire {chemin_pdf}: {e}"))
        return ""


def evaluer_cv(cv_text):
    """
    Evaluates a resume in two steps: reasoning generation and score extraction.

    Args:
        cv_text (str): Raw text extracted from the PDF.

    Returns:
        tuple: (float: Final score out of 100, str: Detailed analysis).
    """

    system_prompt = EVALUATION_CRITERION

    user_prompt = f"""Voici le CV du candidat :
    --- DÉBUT DU CV ---
    {cv_text}
    --- FIN DU CV ---

    MISSION :
    Tu dois évaluer ce CV en remplissant EXACTEMENT le formulaire ci-dessous.
    Interdiction de faire des tableaux. Copie le texte ci-dessous et remplace les crochets par ton texte (2 phrases max) et les "X" par tes notes. Si l'info n'y est pas, essaie tout de même de l'évaluer avec ce dont tu dispose et de mettre une note sur le barême donné.

    Recherche (nombre, qualité et originalité des publications et adéquation au profil): [Analyse] -> Note: X/25
    Enseignement (Responsabilité de modules, création de contenu, adéquation au profil): [Analyse] -> Note: X/25
    Publications: [Analyse] -> Note: X/25
    Niveau de langue (La mise en page n'est pasprise en compte, on se concentre sur le niveau de langue et la clareté du dossier): [Analyse] -> Note: X/15
    Rayonnement (participation à des colloques et niveau des colloques): [Analyse] -> Note: X/10

    Points forts: [Liste]
    Faiblesses: [Liste]
    """

    try:
        response = ollama.chat(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            options={
                "temperature": 0.15,
            },
        )

        analyse = response["message"]["content"].strip()
        print("\n--- ANALYSE ---\n", analyse)

        score_prompt = f"""
        Voici une évaluation :
        {analyse}
        
        MISSION :
        Cherche les notes sous la forme "Note: X/25", "Note: X/15" et "Note: X/10".
        Additionne ces 5 nombres mathématiquement.
        Renvoie UNIQUEMENT le nombre final de la somme (ex: 68.5). Aucun texte.
        Si tu ne trouves pas les notes, renvoie 0.
        """

        response_score = ollama.chat(
            model=MODEL_ID,
            messages=[
                {"role": "user", "content": score_prompt}
            ],
            options={"temperature": 0.0, "num_predict": 100},
        )

        contenu_score = response_score["message"]["content"].strip()
        print("\n--- SCORE RAW ---\n", contenu_score)

        # Extract only the numbers, handle float parsing
        match = re.search(r"(\d{1,3}(?:[\.,]\d+)?)", contenu_score)
        note = float(match.group(1).replace(",", ".")) if match else 0.0

        if match:
            note = float(match.group(1).replace(",", "."))
        else:
            note = 0.0

        return note, analyse
    
    except Exception as e:
        return 0.0, f"Erreur : {str(e)}"


def main():
    # Configuration
    print(blue(f"Vérification/Téléchargement du modèle {MODEL_ID} via Ollama..."))
    try:
        # Downloads if missing, resolves quickly if already present
        ollama.pull(MODEL_ID)
    except Exception as e:
        print(red(f"❌ Erreur lors du pull Ollama : {e}"))
        return

    dossier_data = "data"
    os.makedirs(dossier_data, exist_ok=True)
    resultats = []

    if not os.listdir(dossier_data):
        print(red(f"Le dossier '{dossier_data}' est vide. Ajoute des fichiers PDF."))
        return

    fichiers_pdf = [f for f in os.listdir(dossier_data) if f.lower().endswith(".pdf")]

    if not fichiers_pdf:
        print("Aucun fichier PDF trouvé dans le dossier data.")
        return

    print(f"Début de l'analyse de {len(fichiers_pdf)} CV...")

    for nom_fichier in fichiers_pdf:
        chemin_complet = os.path.join(dossier_data, nom_fichier)
        print(f"Analyse de : {nom_fichier}...")

        texte = extraire_texte_pdf(chemin_complet)
        if texte:
            note, justification = evaluer_cv(texte)
            
            resultats.append({
                "nom_fichier": nom_fichier,
                "chemin": chemin_complet,
                "note": note,
                "justification": justification 
            })
            print(green(f"-> Note : {note}/100"))

    resultats_tries = sorted(resultats, key=lambda x: x["note"], reverse=True)

    with open("classement_cv.json", "w", encoding="utf-8") as f:
        json.dump(resultats_tries, f, indent=4, ensure_ascii=False)

    print(green("\n Analyse terminée !"))
    print(f"Le classement a été sauvegardé dans 'classement_cv.json'.")

    try:
        if platform.system() == 'Darwin':
            subprocess.run(["open", "-a", "TextEdit", "classement_cv.json"])
        elif platform.system() == 'Windows':
            os.startfile("classement_cv.json")
        else:
            print("Pour voir les résultats (Linux) : cat classement_cv.json")
    except Exception as e:
        print(f"Fichier généré, mais impossible de l'ouvrir automatiquement : {e}")


if __name__ == "__main__":
    main()
