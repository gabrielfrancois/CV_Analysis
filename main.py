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
    Évalue ce CV en tant que membre d'un jury académique JUSTE, ANALYTIQUE, mais TRÈS EXIGEANT SUR L'EXCELLENCE SCIENTIFIQUE.

    RÈGLES ABSOLUES :
    1. LE PRINCIPE DE RÉALITÉ : Ce qui n'est pas écrit dans le CV n'existe pas. Tu n'as pas le droit d'écrire "il manque des informations". Si une compétence ou un détail n'y est pas, tu considères simplement que le candidat ne l'a pas fait, et tu évalues factuellement ce qui est présent.
    2. LE DISCERNEMENT : Sois capable de donner une excellente note (35+) à un vrai chercheur publiant dans des revues majeures (comme Q1/Q2), et une mauvaise note (moins de 20) à un profil ne publiant essentiellement que dans des REVUES MINEURS (comme Q3/Q4).
    3. L'OBJECTIVITÉ : Pour l'enseignement, évalue factuellement. Si le profil est junior, c'est normal qu'il n'ait pas dirigé de Master, juge la qualité de ce qu'il a déjà fait.

    Copie-colle EXACTEMENT le formulaire ci-dessous et remplace les [X] par les notes et [...] par ton analyse (2 phrases max).

    Recherche (Nombre, QUALITÉ et prestige des publications. Valorise FORTEMENT les revues internationales comme Q1/Q2. Pénalise FORTEMENT les profils limités au Q3/Q4. Adéquation profil, colloques, projets):
    - Note: [X]/40
    - Analyse: [...]

    Enseignement (Adéquation profil, volume, création de contenus, encadrement. Ajuste tes attentes si c'est un profil junior, mais évalue factuellement ce qui est fait):
    - Note: [X]/40
    - Analyse: [...]

    Qualité du dossier (Clarté, rigueur, qualité du français. Ignore les bugs de l'OCR):
    - Note: [X]/10
    - Analyse: [...]

    Formation initiale (Qualité de la formation, adéquation au profil Génie Civil / Mécanique):
    - Note: [X]/10
    - Analyse: [...]

    Points forts: [...]
    Faiblesses: [...]
    """

    try:
        response = ollama.chat(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            options={"temperature": 0.15},
        )

        analyse = response["message"]["content"].strip()
        print("\n--- ANALYSE ---\n", analyse)

        notes_trouvees = re.findall(r"(\d+(?:[\.,]\d+)?)\s*/\s*(?:40|10)", analyse)

        if len(notes_trouvees) == 4:
            note = sum(float(n.replace(',', '.')) for n in notes_trouvees)
            print(green(f"✅ Python a calculé la note exacte (4/4 critères trouvés) : {note}/100"))
        else:
            print(yellow(f"⚠️ Format imprécis ({len(notes_trouvees)}/4 notes). Passage au calcul par LLM..."))
            
            score_prompt = f"""
            Voici une évaluation :
            {analyse}
            
            MISSION :
            Calcule la note totale sur 100 à partir des éléments ci-dessus.
            Renvoie UNIQUEMENT le chiffre final sans texte ni calculs écrits.
            """

            response_score = ollama.chat(
                model=MODEL_ID,
                messages=[{"role": "user", "content": score_prompt}],
                options={"temperature": 0.0, "num_predict": 50},
            )

            contenu_score = response_score["message"]["content"].strip()
            print(cyan(f"--- SCORE RAW (LLM Fallback) ---\n{contenu_score}"))

            match = re.search(r"(\d{1,3}(?:[\.,]\d+)?)", contenu_score)
            note = float(match.group(1).replace(",", ".")) if match else 0.0

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
