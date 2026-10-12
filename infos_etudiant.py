from pathlib import Path
import pandas as pd
from etudiants import Eleve
from pandas_base_de_donnee import FICHIER

class InfoEtudiant(Eleve):
    def __init__(self, nom, prenom, classe, adresse="", contact="", contact_parents=""):
        super().__init__(nom, prenom, classe)
        self.adresse = adresse
        self.contact = contact
        self.contact_parents = contact_parents

    def enregistrer_infos(self, numero):
        """Ajoute ou met à jour les infos complémentaires de l'étudiant."""
        try:
            df_infos = pd.read_excel(FICHIER, sheet_name="Infos_Etudiants", engine="openpyxl")
        except (FileNotFoundError, ValueError):
            df_infos = pd.DataFrame(columns=["Numero", "Nom", "Prenom", "Adresse", "Contact", "Contact_Parents"])

        # Vérifier si l'étudiant a déjà une ligne d'infos
        if "Numero" in df_infos.columns and numero in df_infos["Numero"].values:
            # Mise à jour
            df_infos.loc[df_infos["Numero"] == numero, ["Nom", "Prenom", "Adresse", "Contact", "Contact_Parents"]] = [
                self.nom, self.prenom, self.adresse, self.contact, self.contact_parents
            ]
        else:
            # Ajout
            nouvelle_ligne = pd.DataFrame({
                "Numero": [numero],
                "Nom": [self.nom],
                "Prenom": [self.prenom],
                "Adresse": [self.adresse],
                "Contact": [self.contact],
                "Contact_Parents": [self.contact_parents]
            })
            df_infos = pd.concat([df_infos, nouvelle_ligne], ignore_index=True)

        with pd.ExcelWriter(FICHIER, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df_infos.to_excel(writer, sheet_name="Infos_Etudiants", index=False)

        print(f"Infos de l'étudiant {self.nom} {self.prenom} enregistrées.")

    @staticmethod
    def charger_infos(numero):
        """Charge les infos existantes d'un étudiant, retourne un objet InfoEtudiant ou None."""
        try:
            df_infos = pd.read_excel(FICHIER, sheet_name="Infos_Etudiants", engine="openpyxl")
        except (FileNotFoundError, ValueError):
            return None
        ligne = df_infos[df_infos["Numero"] == numero]
        if ligne.empty:
            return None
        ligne = ligne.iloc[0]
        return InfoEtudiant(
            ligne["Nom"], ligne["Prenom"], "",  # la classe sera récupérée via Eleve si besoin
            adresse=ligne["Adresse"],
            contact=ligne["Contact"],
            contact_parents=ligne["Contact_Parents"]
        )