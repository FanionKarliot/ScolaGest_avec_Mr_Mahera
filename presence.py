import pandas as pd
from datetime import datetime

from pandas_base_de_donnee import (
    FEUILLE_PRESENCES, lire_feuille, ecrire_feuille,
)

COLONNES_PRESENCES = [
    "Date", "Numero", "Nom", "Prenom", "Classe",
    "Statut", "Justification",
]

STATUTS = ["Présent", "Absent", "Retard", "Justifié"]

# Colonnes texte à forcer en object (pour éviter les NaN float)
_COLS_TEXTE = ["Date", "Nom", "Prenom", "Classe", "Statut", "Justification"]


def _preparer_df(df):
    """Force les colonnes texte en object + remplace les NaN par ''."""
    if df.empty:
        return pd.DataFrame(columns=COLONNES_PRESENCES)
    for col in _COLS_TEXTE:
        if col in df.columns:
            df[col] = df[col].astype(object).where(df[col].notna(), "")
        else:
            df[col] = ""
    if "Numero" in df.columns:
        df["Numero"] = pd.to_numeric(df["Numero"], errors="coerce")
    return df


class Presence:
    """Gère la feuille de présence d'un étudiant pour une date donnée."""

    def __init__(self, date, numero, nom, prenom, classe,
                 statut="Présent", justification=""):
        self.date = date
        self.numero = int(numero)
        self.nom = nom
        self.prenom = prenom
        self.classe = classe
        self.statut = statut
        self.justification = justification

    def enregistrer(self):
        df = _preparer_df(lire_feuille(FEUILLE_PRESENCES, COLONNES_PRESENCES))
        nouvelle_ligne = {
            "Date": str(self.date),
            "Numero": self.numero,
            "Nom": self.nom,
            "Prenom": self.prenom,
            "Classe": self.classe,
            "Statut": self.statut,
            "Justification": self.justification or "",
        }

        if not df.empty:
            masque = (df["Date"].astype(str) == str(self.date)) & \
                     (pd.to_numeric(df["Numero"], errors="coerce") == self.numero)
            if masque.any():
                idx = df.index[masque][0]
                for k, v in nouvelle_ligne.items():
                    df.at[idx, k] = v
                ecrire_feuille(df, FEUILLE_PRESENCES)
                return

        df = pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True)
        ecrire_feuille(df, FEUILLE_PRESENCES)

    @staticmethod
    def enregistrer_lot(date, classe, enregistrements):
        """Enregistre plusieurs présences d'un coup."""
        df = _preparer_df(lire_feuille(FEUILLE_PRESENCES, COLONNES_PRESENCES))

        for r in enregistrements:
            num = int(r["numero"])
            nouvelle_ligne = {
                "Date": str(date),
                "Numero": num,
                "Nom": r["nom"],
                "Prenom": r["prenom"],
                "Classe": classe,
                "Statut": r["statut"],
                "Justification": r.get("justification", "") or "",
            }
            if not df.empty:
                masque = (df["Date"].astype(str) == str(date)) & \
                         (pd.to_numeric(df["Numero"], errors="coerce") == num)
                if masque.any():
                    idx = df.index[masque][0]
                    for k, v in nouvelle_ligne.items():
                        df.at[idx, k] = v
                    continue
            df = pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True)

        ecrire_feuille(df, FEUILLE_PRESENCES)

    @staticmethod
    def charger_pour_date_classe(date, classe):
        df = _preparer_df(lire_feuille(FEUILLE_PRESENCES, COLONNES_PRESENCES))
        if df.empty:
            return {}
        masque = (df["Date"].astype(str) == str(date)) & \
                 (df["Classe"].astype(str).str.lower() == classe.lower())
        sous = df[masque]
        return {int(r["Numero"]): r["Statut"] for _, r in sous.iterrows()}

    @staticmethod
    def charger_justifications_pour_date_classe(date, classe):
        df = _preparer_df(lire_feuille(FEUILLE_PRESENCES, COLONNES_PRESENCES))
        if df.empty:
            return {}
        masque = (df["Date"].astype(str) == str(date)) & \
                 (df["Classe"].astype(str).str.lower() == classe.lower())
        sous = df[masque]
        return {int(r["Numero"]): str(r["Justification"]) for _, r in sous.iterrows()}

    @staticmethod
    def statistiques_etudiant(numero):
        df = _preparer_df(lire_feuille(FEUILLE_PRESENCES, COLONNES_PRESENCES))
        if df.empty:
            return (0, 0, 0, 0, 0.0)
        sous = df[pd.to_numeric(df["Numero"], errors="coerce") == int(numero)]
        if sous.empty:
            return (0, 0, 0, 0, 0.0)
        counts = sous["Statut"].value_counts().to_dict()
        pres = counts.get("Présent", 0)
        abs_ = counts.get("Absent", 0)
        ret = counts.get("Retard", 0)
        jus = counts.get("Justifié", 0)
        total = len(sous)
        taux = ((pres + ret + jus) / total * 100) if total else 0.0
        return (pres, abs_, ret, jus, round(taux, 1))

    @staticmethod
    def statistiques_par_classe(classe):
        df = _preparer_df(lire_feuille(FEUILLE_PRESENCES, COLONNES_PRESENCES))
        if df.empty:
            return []
        sous = df[df["Classe"].astype(str).str.lower() == classe.lower()]
        if sous.empty:
            return []
        res = []
        for num, groupe in sous.groupby("Numero"):
            total = len(groupe)
            pres = (groupe["Statut"].isin(["Présent", "Retard", "Justifié"])).sum()
            taux = round(pres / total * 100, 1) if total else 0.0
            ligne = groupe.iloc[0]
            res.append((int(num), ligne["Nom"], ligne["Prenom"], taux))
        res.sort(key=lambda t: t[3], reverse=True)
        return res