from pathlib import Path
import pandas as pd
import numpy as np

from pandas_base_de_donnee import FICHIER

class Eleve:
    def __init__(self, nom, prenom, classe):
        self.nom = nom
        self.prenom = prenom
        self.classe = classe
        
    def inscription(self):
        # 1. Lecture sécurisée de la feuille "Etudiants"
        # 2. Calcul du prochain numéro (bonne pratique : utiliser max() et non la dernière ligne)
        # 3. Création de la nouvelle ligne
        # 4. Concaténation
        # 5. Écriture sans écraser les autres feuilles (mode 'a')
        
        print("Ajout d'étudiant vers Excel")
        
        try:
            df_inscription = pd.read_excel(FICHIER, sheet_name="Etudiants", engine="openpyxl")
        except (FileNotFoundError, ValueError):
            df_inscription = pd.DataFrame(columns=["Numero", "Nom", "Prenom", "Classe"])

        if df_inscription.empty:
            prochain_numero = 1
        else:
            df_inscription["Numero"] = pd.to_numeric(df_inscription["Numero"], errors="coerce")
            dernier = df_inscription["Numero"].max()
            prochain_numero = int(dernier) + 1 if pd.notna(dernier) else 1
            
        etudiant_existe = False
        
        for etudiant in df_inscription.itertuples(index=False): # crée un itérateur (Permet de parcourir les lignes du DataFrame5.
            if (etudiant.Nom == self.nom and 
                etudiant.Prenom == self.prenom and 
                etudiant.Classe == self.classe):
                
                etudiant_existe = True
                break

        if not etudiant_existe:
            nouvel_ligne = pd.DataFrame({
                "Numero": [prochain_numero],
                "Nom": [self.nom],
                "Prenom": [self.prenom],
                "Classe": [self.classe],
            })

            df_inscription = pd.concat([df_inscription, nouvel_ligne], ignore_index=True)

            with pd.ExcelWriter(FICHIER, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df_inscription.to_excel(writer, sheet_name="Etudiants", index=False)

            print(f"Étudiant ajouté avec le numéro {prochain_numero}")
            # print(df_inscription.tail())
            
        else:
            print("L'étudiant existe déjà dans la base de données.")
        
    def afficher_les_etudiants():
        print("Affichages des etudiants")
        df_etudiants = pd.read_excel(FICHIER, sheet_name="Etudiants", engine="openpyxl")
        # print(df_etudiants.head())
        
    def etudiant(numero):
        df_etudiants = pd.read_excel(FICHIER, sheet_name="Etudiants", engine="openpyxl")
        etudiant = df_etudiants[df_etudiants["Numero"] == numero]
        if not etudiant.empty:
            nom = etudiant.iloc[0]["Nom"]
            prenom = etudiant.iloc[0]["Prenom"]
            classe = etudiant.iloc[0]["Classe"]
            return Eleve(nom, prenom, classe)
        else:
            return None
    
    def verification_numero_etudiant(numero):
        df_etudiants = pd.read_excel(FICHIER, sheet_name="Etudiants", engine="openpyxl")
        numero_existant = False
        
        for i in range(len(df_etudiants["Numero"])):
            if df_etudiants.loc[i, "Numero"] == numero:
                numero_existant = True
                break
        
        return numero_existant
        
    def obtenir_classes_existantes():
        """Retourne la liste des classes uniques présentes dans le fichier."""
        try:
            df_etudiants = pd.read_excel(FICHIER, sheet_name="Etudiants", engine="openpyxl")
            if "Classe" in df_etudiants.columns:
                classes = df_etudiants["Classe"].dropna().unique().tolist()
                classes.sort()
                return classes
            else:
                return []
        except Exception:
            return []
        
    @staticmethod
    def rechercher_par_nom_prenom(nom="", prenom=""):
        """
        Recherche des étudiants par nom et/ou prénom (partiel, insensible à la casse).
        Retourne une liste de tuples (numero, nom, prenom, classe).
        """
        try:
            df_etudiants = pd.read_excel(FICHIER, sheet_name="Etudiants", engine="openpyxl")
        except Exception:
            return []

        # Filtre sur le nom
        if nom:
            df_etudiants = df_etudiants[
                df_etudiants["Nom"].astype(str).str.lower().str.contains(nom.lower(), na=False)
            ]
        # Filtre sur le prénom
        if prenom:
            df_etudiants = df_etudiants[
                df_etudiants["Prenom"].astype(str).str.lower().str.contains(prenom.lower(), na=False)
            ]

        # Conversion des numéros en entiers (ils peuvent être lus comme float)
        df_etudiants["Numero"] = pd.to_numeric(df_etudiants["Numero"], errors="coerce")
        df_etudiants = df_etudiants.dropna(subset=["Numero"])
        df_etudiants["Numero"] = df_etudiants["Numero"].astype(int)

        resultats = []
        for _, row in df_etudiants.iterrows():
            resultats.append((row["Numero"], row["Nom"], row["Prenom"], row["Classe"]))
        return resultats
    
    @staticmethod
    def obtenir_etudiants_par_classe(classe):
        """
        Retourne une liste de tuples (numero, nom, prenom, classe)
        pour tous les étudiants de la classe donnée.
        """
        try:
            df_etudiants = pd.read_excel(FICHIER, sheet_name="Etudiants", engine="openpyxl")
        except Exception:
            return []

        # Filtrer par classe (insensible à la casse)
        if classe:
            df_etudiants = df_etudiants[
                df_etudiants["Classe"].astype(str).str.lower() == classe.lower()
            ]
        else:
            df_etudiants = pd.DataFrame()

        df_etudiants["Numero"] = pd.to_numeric(df_etudiants["Numero"], errors="coerce")
        df_etudiants = df_etudiants.dropna(subset=["Numero"])
        df_etudiants["Numero"] = df_etudiants["Numero"].astype(int)

        resultats = []
        for _, row in df_etudiants.iterrows():
            resultats.append((row["Numero"], row["Nom"], row["Prenom"], row["Classe"]))
        return resultats