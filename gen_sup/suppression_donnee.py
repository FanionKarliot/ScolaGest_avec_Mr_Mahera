"""
suppression_donnee.py
---------------------
Script utilitaire permettant de vider toutes les données
des feuilles du classeur Excel tout en conservant
les en-têtes (noms des colonnes).

Utilisation (depuis n'importe où) :
    python gen_sup/suppression_donnee.py
"""

from pathlib import Path
from datetime import datetime
import shutil
import sys
import os

# ============================================================================
#  AJOUT DE LA RACINE DU PROJET AU sys.path  (indispensable depuis gen_sup/)
# ============================================================================
RACINE_PROJET = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE_PROJET))

# Se placer dans la racine du projet pour que pandas_base_de_donnee.py
# trouve bien ./document/notes_etudiant_exemple.xlsx
os.chdir(RACINE_PROJET)

# ============================================================================
#  IMPORTS (après ajustement du sys.path)
# ============================================================================
import pandas as pd
from pandas_base_de_donnee import FICHIER  # chemin officiel du projet


# ================== CONFIGURATION ==================
FAIRE_UNE_SAUVEGARDE = True
DOSSIER_SAUVEGARDE = RACINE_PROJET / "document" / "sauvegardes"

# None = toutes les feuilles ; sinon liste explicite
FEUILLES_A_VIDER = None

# 0 = feuille totalement vidée (en-têtes seuls)
LIGNES_A_CONSERVER = 0


# ================== FONCTIONS ==================
def verifier_fichier(chemin: Path) -> None:
    if not chemin.exists():
        print(f"❌ Fichier introuvable : {chemin}")
        sys.exit(1)


def faire_sauvegarde(chemin: Path) -> Path:
    DOSSIER_SAUVEGARDE.mkdir(parents=True, exist_ok=True)
    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    nom_sauvegarde = f"{chemin.stem}_backup_{horodatage}{chemin.suffix}"
    chemin_sauvegarde = DOSSIER_SAUVEGARDE / nom_sauvegarde
    shutil.copy2(chemin, chemin_sauvegarde)
    print(f"💾 Sauvegarde créée : {chemin_sauvegarde}")
    return chemin_sauvegarde


def lister_feuilles(chemin: Path) -> list[str]:
    with pd.ExcelFile(chemin, engine="openpyxl") as xls:
        return xls.sheet_names


def vider_feuille(df: pd.DataFrame, lignes_a_conserver: int = 0) -> pd.DataFrame:
    colonnes = df.columns.tolist()
    if lignes_a_conserver > 0 and not df.empty:
        return df.head(lignes_a_conserver).reset_index(drop=True)
    return pd.DataFrame(columns=colonnes)


def vider_toutes_les_feuilles(chemin: Path, feuilles=None, lignes_a_conserver=0):
    with pd.ExcelFile(chemin, engine="openpyxl") as xls:
        feuilles_cibles = feuilles if feuilles else xls.sheet_names

    resultats = {}
    for nom in feuilles_cibles:
        try:
            df = pd.read_excel(chemin, sheet_name=nom, engine="openpyxl")
            avant = len(df)
            df_vide = vider_feuille(df, lignes_a_conserver)
            resultats[nom] = df_vide
            print(f"  ▸ Feuille « {nom} » : {avant} ligne(s) → {len(df_vide)} ligne(s)")
        except Exception as e:
            print(f"  ⚠️  Feuille « {nom} » ignorée (erreur : {e})")

    with pd.ExcelWriter(chemin, engine="openpyxl", mode="w") as writer:
        for nom, df_vide in resultats.items():
            df_vide.to_excel(writer, sheet_name=nom, index=False)

    print(f"\n✅ {len(resultats)} feuille(s) vidée(s) dans : {chemin}")


# ================== MAIN ==================
def main():
    print("=" * 55)
    print("  🧹  NETTOYAGE DES DONNÉES EXCEL — ScolaGest")
    print("=" * 55)
    print(f"📂 Racine du projet : {RACINE_PROJET}")
    print(f"📂 Fichier ciblé    : {FICHIER}\n")

    verifier_fichier(FICHIER)

    if FAIRE_UNE_SAUVEGARDE:
        faire_sauvegarde(FICHIER)
        print()

    feuilles = lister_feuilles(FICHIER)
    cibles = FEUILLES_A_VIDER if FEUILLES_A_VIDER else feuilles
    print(f"📋 Feuilles à vider ({len(cibles)}) : {', '.join(cibles)}\n")

    confirmation = input("⚠️  Confirmer la suppression des données ? (oui/non) : ").strip().lower()
    if confirmation not in ("oui", "o", "yes", "y"):
        print("❌ Opération annulée.")
        sys.exit(0)

    print("\n🔄 Traitement en cours...\n")
    vider_toutes_les_feuilles(FICHIER, cibles, LIGNES_A_CONSERVER)
    print("\n🎉 Terminé avec succès.")


if __name__ == "__main__":
    main()