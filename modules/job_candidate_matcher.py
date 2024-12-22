import re
from groq import Groq
import json
from dotenv import load_dotenv
load_dotenv()


def extract_score(full_output):
    """
    Extrait le score de compatibilité d'une chaîne de texte.
    """
    match = re.search(r"\b\d+(\.\d+)?\b", full_output)
    if match:
        return float(match.group(0))
    else:
        print("Score non trouvé dans la réponse.")
        return None


def result_with_llama(api_k, offre, candidat):
    """
    Fonction pour obtenir un score de compatibilité entre une offre et un candidat via l'API Groq (Llama).
    
    Paramètres
    ----------
    api_k : str
        La clé API pour l'authentification avec l'API Llama.
    offre : dict
        Les informations de l'offre d'emploi.
    candidat : dict
        Les informations du candidat.
    
    Retourne
    -------
    float
        Le score de compatibilité entre l'offre et le candidat.
    """
    client = Groq(api_key=api_k)

    prompt = f"""
    Tu es un expert en ressources humaines. J'ai une offre d'emploi et un profil de candidat. 
    Tu dois évaluer le score de compatibilité entre le candidat et l'offre en te basant sur les critères suivants :

    - Compétences : Compare les compétences du candidat avec celles requises par l'offre. Donne plus de poids aux compétences essentielles.
    - Expérience : Vérifie si le candidat a l'expérience minimale requise pour le poste.
    - Certifications : Assure-toi que les certifications du candidat correspondent à celles demandées dans l'offre.
    - Localisation : Évalue si la localisation du candidat est compatible avec le lieu de travail indiqué.
    - Langues : Vérifie si le candidat parle les langues requises dans l'offre.

    Utilise un score de 0 à 10, où 0 signifie que le candidat n'est pas du tout compatible et 10 signifie qu'il est parfaitement compatible avec l'offre. 
    Ne donne pas d'explication, seulement un score.

    Offre d'emploi : 
    {json.dumps(offre, ensure_ascii=False, indent=2)}

    Profil du candidat :
    {json.dumps(candidat, ensure_ascii=False, indent=2)}
    """
    completion = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {
                "role": "user",
                "content": prompt
            },
            {
                "role": "assistant",
                "content": ""
            }
        ],
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stream=True,
        stop=None,
    )
  
    full_output = ""
    for chunk in completion:
        output = chunk.choices[0].delta.content or ""
        full_output += output

    score = extract_score(full_output)
    return score
