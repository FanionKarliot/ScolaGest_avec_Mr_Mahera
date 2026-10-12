> **Application de bureau** permettant la gestion centralisée des étudiants, des notes, des présences et de la comptabilité scolaire d'un établissement.
> Développée en **Python** avec **Tkinter**, **Pandas**, **openpyxl** et **ReportLab**.

# ✨ Fonctionnalités

| Module | Description |
|---|---|
| 📝 **Inscription** | Ajout d'un étudiant avec attribution automatique d'un numéro matricule et contrôle d'unicité |
| 📊 **Notes** | Saisie des notes dans 6 matières (Math, PC, HG, Malagasy, Français, Philo) avec validation 0–20 |
| 🔍 **Recherche** | Recherche d'un étudiant par nom et/ou prénom (saisie partielle, insensible à la casse) |
| ℹ️ **Informations étudiant** | Gestion de l'adresse, du contact personnel et du contact des parents |
| 💰 **Comptabilité** | Suivi des frais de scolarité, versements, reste à payer et statut (*Impayé*, *Partiel*, *Soldé*) |
| ✅ **Présences** | Appel journalier avec 4 statuts (*Présent*, *Absent*, *Retard*, *Justifié*) et calcul du taux de présence |
| 📄 **Génération PDF** | Création de listes de classe prêtes à imprimer via ReportLab |

---

## 🛠️ Technologies utilisées

| Technologie | Version | Usage |
|---|---|---|
| **Python** | 3.10+ | Langage principal |
| **Tkinter / ttk** | intégré | Interface graphique |
| **Pandas** | ≥ 2.0 | Manipulation des données tabulaires |
| **NumPy** | ≥ 1.24 | Calculs statistiques |
| **openpyxl** | ≥ 3.1 | Lecture / écriture des fichiers Excel |
| **ReportLab** | ≥ 4.0 | Génération des documents PDF |

---

## 📦 Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/FanionKarliot/ScolaGest_avec_Mr_Mahera/tree/main
cd scolagest
```

### 2. Créer un environnement virtuel (recommandé)

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

> **Remarque :** sous **Linux**, `tkinter` doit être installé séparément :
> ```bash
> sudo apt install python3-tk
> ```


## 🚀 Lancement de l'application

```bash
python main.py
```

L'application s'ouvre sur le **tableau de bord**, avec une navigation latérale et les raccourcis clavier suivants :

| Raccourci | Action |
|---|---|
| `Ctrl + 1` à `Ctrl + 6` | Naviguer entre les pages |
| `Ctrl + B` | Afficher / masquer la barre latérale |
| `Entrée` | Valider le formulaire actif |

---

## 📁 Structure du projet

```
scolagest/
│
├── document/
│   ├── notes_etudiant_exemple.xlsx        # Base de données principale (non versionnée)
│   └── sauvegardes/                       # Sauvegardes automatiques (non versionnées)
│
├── gen_sup/                               # Scripts utilitaires
│   ├── generer_donnees.py                 # Génération de données fictives
│   └── suppression_donnee.py              # Nettoyage du fichier Excel
│
├── main.py                                # Interface graphique principale
├── etudiants.py                           # Gestion des inscriptions
├── notes.py                               # Gestion des notes
├── infos_etudiant.py                      # Informations complémentaires
├── comptabilite.py                        # Suivi des frais scolaires
├── presence.py                            # Suivi des présences
├── generateur_pdf.py                      # Génération de PDF
├── pandas_base_de_donnee.py               # Couche d'accès aux données
│
├── requirements.txt                       # Dépendances Python
├── .gitignore                             # Fichiers exclus de Git
└── README.md                              # Ce fichier
```