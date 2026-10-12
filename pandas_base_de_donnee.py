from pathlib import Path
import pandas as pd

# Chemin du fichier Excel
FICHIER = Path("./document/notes_etudiant_exemple.xlsx")

# Noms des feuilles (centralisés pour éviter les typos)
FEUILLE_ETUDIANTS   = "Etudiants"
FEUILLE_NOTES       = "Notes"
FEUILLE_INFOS       = "Infos_Etudiants"
FEUILLE_COMPTA      = "Comptabilite"
FEUILLE_PRESENCES   = "Presences"


def nettoyer_colonnes(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("'", "", regex=False)
    )
    return df


def lire_feuille(nom_feuille, colonnes_par_defaut=None):
    """
    Lit une feuille Excel. Si elle n'existe pas, retourne un DataFrame vide
    avec les colonnes fournies.
    """
    try:
        return pd.read_excel(FICHIER, sheet_name=nom_feuille, engine="openpyxl")
    except (FileNotFoundError, ValueError):
        if colonnes_par_defaut:
            return pd.DataFrame(columns=colonnes_par_defaut)
        return pd.DataFrame()


def ecrire_feuille(df, nom_feuille):
    """Écrit un DataFrame dans une feuille sans écraser les autres."""
    with pd.ExcelWriter(FICHIER, engine="openpyxl", mode="a",
                        if_sheet_exists="replace") as writer:
        df.to_excel(writer, sheet_name=nom_feuille, index=False)
        

def lire_toutes_les_donnees():
    """Retourne un dict avec toutes les feuilles lues (DataFrames vides si absentes)."""
    feuilles = {
        "etudiants": ["Numero", "Nom", "Prenom", "Classe"],
        "notes": ["Numero", "Math", "PC", "HG", "Malagasy", "Francais", "Philo"],
        "comptabilite": ["Numero", "Frais_Total", "Montant_Paye", "Reste", "Statut"],
        "presences": ["Numero", "Classe", "Statut"],
    }
    resultat = {}
    for nom, cols in feuilles.items():
        try:
            resultat[nom] = pd.read_excel(FICHIER, sheet_name=nom.capitalize(), engine="openpyxl")
        except Exception:
            resultat[nom] = pd.DataFrame(columns=cols)
    # Le nom exact des feuilles diffère (Etudiants, Notes, Comptabilite, Presences)
    try:
        resultat["etudiants"] = pd.read_excel(FICHIER, sheet_name="Etudiants", engine="openpyxl")
    except Exception:
        resultat["etudiants"] = pd.DataFrame(columns=feuilles["etudiants"])
    try:
        resultat["notes"] = pd.read_excel(FICHIER, sheet_name="Notes", engine="openpyxl")
    except Exception:
        resultat["notes"] = pd.DataFrame(columns=feuilles["notes"])
    try:
        resultat["comptabilite"] = pd.read_excel(FICHIER, sheet_name="Comptabilite", engine="openpyxl")
    except Exception:
        resultat["comptabilite"] = pd.DataFrame(columns=feuilles["comptabilite"])
    try:
        resultat["presences"] = pd.read_excel(FICHIER, sheet_name="Presences", engine="openpyxl")
    except Exception:
        resultat["presences"] = pd.DataFrame(columns=feuilles["presences"])
    return resultat