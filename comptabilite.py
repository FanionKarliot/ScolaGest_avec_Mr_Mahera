import pandas as pd
from datetime import datetime

from pandas_base_de_donnee import (
    FEUILLE_COMPTA, FEUILLE_ETUDIANTS,
    lire_feuille, ecrire_feuille,
)

COLONNES_COMPTA = [
    "Numero", "Nom", "Prenom", "Classe",
    "Frais_Total", "Montant_Paye", "Reste",
    "Statut", "Date_Paiement", "Observation",
]


class Paiement:
    """Gère les frais scolaires d'un étudiant."""

    def __init__(self, numero, nom, prenom, classe,
                 frais_total, montant_paye, date_paiement=None,
                 observation=""):
        self.numero = int(numero)
        self.nom = nom
        self.prenom = prenom
        self.classe = classe
        self.frais_total = float(frais_total)
        self.montant_paye = float(montant_paye)
        self.date_paiement = date_paiement or datetime.now().strftime("%d/%m/%Y")
        self.observation = observation

    # ----- Propriétés calculées -----
    @property
    def reste(self):
        return max(0.0, self.frais_total - self.montant_paye)

    @property
    def statut(self):
        if self.montant_paye <= 0:
            return "Impayé"
        elif self.montant_paye < self.frais_total:
            return "Partiel"
        return "Soldé"

    # ----- Écriture -----
    def enregistrer(self):
        """Ajoute ou met à jour la ligne de comptabilité pour cet étudiant."""
        df = lire_feuille(FEUILLE_COMPTA, COLONNES_COMPTA)

        nouvelle_ligne = {
            "Numero": self.numero,
            "Nom": self.nom,
            "Prenom": self.prenom,
            "Classe": self.classe,
            "Frais_Total": self.frais_total,
            "Montant_Paye": self.montant_paye,
            "Reste": self.reste,
            "Statut": self.statut,
            "Date_Paiement": self.date_paiement,
            "Observation": self.observation,
        }

        if not df.empty and self.numero in df["Numero"].astype(int).values:
            # Mise à jour
            idx = df.index[df["Numero"].astype(int) == self.numero][0]
            for k, v in nouvelle_ligne.items():
                df.at[idx, k] = v
        else:
            # Ajout
            df = pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True)

        ecrire_feuille(df, FEUILLE_COMPTA)
        print(f"💾 Comptabilité enregistrée pour {self.prenom} {self.nom} — {self.statut}")

    # ----- Lecture -----
    @staticmethod
    def charger(numero):
        """Retourne un objet Paiement ou None."""
        df = lire_feuille(FEUILLE_COMPTA, COLONNES_COMPTA)
        if df.empty:
            return None
        ligne = df[df["Numero"].astype(int) == int(numero)]
        if ligne.empty:
            return None
        r = ligne.iloc[0]
        return Paiement(
            r["Numero"], r["Nom"], r["Prenom"], r["Classe"],
            r["Frais_Total"], r["Montant_Paye"],
            r.get("Date_Paiement"), r.get("Observation", "")
        )

    @staticmethod
    def lister_tous():
        """Retourne la liste de tous les paiements enregistrés."""
        df = lire_feuille(FEUILLE_COMPTA, COLONNES_COMPTA)
        if df.empty:
            return []
        return df.to_dict("records")

    @staticmethod
    def ajouter_versement(numero, montant_sup, observation=""):
        """Ajoute un versement au montant déjà payé."""
        p = Paiement.charger(numero)
        if p is None:
            raise ValueError("Aucun dossier de comptabilité pour cet étudiant. "
                             "Créez d'abord son dossier initial.")
        p.montant_paye += float(montant_sup)
        p.date_paiement = datetime.now().strftime("%d/%m/%Y")
        if observation:
            p.observation = (p.observation + " | " if p.observation else "") + observation
        p.enregistrer()
        return p