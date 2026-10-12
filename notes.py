from pathlib import Path
import pandas as pd
import numpy as np
from etudiants import Eleve

from pandas_base_de_donnee import FICHIER

class Note:
    def __init__(self, numero, nom, prenom, note_math, note_pc, note_hg, note_malagasy, note_francais, note_philo):
        self.numero = numero
        self.nom = nom
        self.prenom = prenom
        self.__note_math = note_math
        self.__note_pc = note_pc
        self.__note_hg = note_hg
        self.__note_malagasy = note_malagasy
        self.__note_francais = note_francais
        self.__note_philo = note_philo
        
    @property
    def note_math(self):
        return self.__note_math

    @property
    def note_pc(self):
        return self.__note_pc
    
    @property
    def note_hg(self):
        return self.__note_hg
        
    @property
    def note_math(self):
        return self.__note_math
    
    @property
    def note_malagasy(self):
        return self.__note_malagasy
    
    @property
    def note_francais(self):
        return self.__note_francais
    
    @property
    def note_philo(self):
        return self.__note_philo
    
    def afficher_les_notes():
        print("Affichages des notes")
        df_notes = pd.read_excel(FICHIER, sheet_name="Notes", engine="openpyxl")
        print(df_notes.head())
    
    def ajout_de_note(self):
        try:
            df_notes = pd.read_excel(FICHIER, sheet_name="Notes", engine="openpyxl")
        except (FileNotFoundError, ValueError):
            df_notes = pd.DataFrame(columns=["Numero", "Nom", "Prenom", "Math", "PC", "HG", "Malagasy", "Francais", "Philo"])
        
        df_etudiants = pd.read_excel(FICHIER, sheet_name="Etudiants", engine="openpyxl")
        numero_existant = False
        
        for i in range(len(df_etudiants["Numero"])):
            if df_etudiants.loc[i, "Numero"] == self.numero:
                numero_existant = True
                break
            else:
                numero_existant = False
                print("Le numero d'etudiant n'existe pas")
        
        if numero_existant:
            nouvel_ligne = pd.DataFrame({
                "Numero": [self.numero],
                "Nom": [self.nom],
                "Prenom": [self.prenom],
                "Math": [self.note_math],
                "PC": [self.note_pc],
                "HG": [self.note_hg],
                "Malagasy": [self.note_malagasy],
                "Francais": [self.note_francais],
                "Philo": [self.note_philo]
            })
            
            df_notes = pd.concat([df_notes, nouvel_ligne], ignore_index=True)
            with pd.ExcelWriter(FICHIER, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df_notes.to_excel(writer, sheet_name="Notes", index=False)
        
        
        print("=========df_notes")
        print(df_notes.head())
    
    def afficher_les_notes_d_un_etudiant(numero_etudiant: int, etudiant: Eleve) -> "Note | None":
        """Retourne un objet Note contenant les notes de l'étudiant, ou None si absent."""
        df_notes = pd.read_excel(FICHIER, sheet_name="Notes", engine="openpyxl")
        etudiant_notes = df_notes.loc[df_notes["Numero"] == numero_etudiant]

        if etudiant_notes.empty:
            return None

        # On suppose qu'il n'y a qu'une seule ligne par étudiant (sinon prendre .iloc[0])
        ligne = etudiant_notes.iloc[0]
        return Note(
            numero_etudiant,
            etudiant.nom,
            etudiant.prenom,
            ligne["Math"],
            ligne["PC"],
            ligne["HG"],
            ligne["Malagasy"],
            ligne["Francais"],
            ligne["Philo"]
        )