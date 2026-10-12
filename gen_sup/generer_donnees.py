"""
Génère des données réalistes pour ScolaGest (étudiants, notes, infos,
comptabilité, présences) en utilisant TES classes existantes :
Eleve, Note, InfoEtudiant, Paiement, Presence.

Utilisation (depuis n'importe où) :

    python gen_sup/generer_donnees.py
    python gen_sup/generer_donnees.py --reset
    python gen_sup/generer_donnees.py --reset --par-classe 20

--reset ne supprime rien définitivement : les fichiers de données sont DÉPLACÉS
dans un dossier  document/sauvegarde_AAAAMMJJ_HHMMSS/  (tu peux les remettre si besoin).
"""
import argparse
import os
import random
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ============================================================================
#  AJOUT DE LA RACINE DU PROJET AU sys.path  (indispensable depuis gen_sup/)
# ============================================================================
RACINE_PROJET = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE_PROJET))

# Se placer à la racine du projet pour que tous les chemins relatifs
# (ex : ./document/notes_etudiant_exemple.xlsx dans pandas_base_de_donnee.py)
# soient correctement résolus.
os.chdir(RACINE_PROJET)

# Dossier où sont stockés les fichiers de données (Excel, etc.)
DOSSIER_DONNEES = RACINE_PROJET / "document"

# ============================================================================
#  IMPORTS (après ajustement du sys.path)
# ============================================================================
from etudiants import Eleve
from notes import Note
from infos_etudiant import InfoEtudiant
from comptabilite import Paiement
from presence import Presence, STATUTS


# ----------------------------------------------------------------------------
# Paramètres (modifie-les librement)
# ----------------------------------------------------------------------------
CLASSES = {
    "Seconde": 420_000,
    "Première A": 480_000,
    "Première S": 500_000,
    "Terminale A": 520_000,
    "Terminale D": 540_000,
}
NB_JOURS_PRESENCE = 10
EXTENSIONS_DONNEES = (".xlsx", ".xls", ".csv", ".json", ".db", ".sqlite")

random.seed(2026)

PRENOMS_F = ["Miora", "Hasina", "Volatiana", "Fanja", "Tsiory", "Nirina", "Lalaina",
             "Mialy", "Aina", "Sarobidy", "Anjara", "Ony", "Rinà", "Haingo", "Zo",
             "Fenitra", "Soa", "Tiana", "Mahefa", "Ravaka", "Marie", "Sandy", "Elise",
             "Josiane", "Noro", "Lova", "Hanta", "Valisoa", "Bodo", "Judith"]
PRENOMS_M = ["Rivo", "Andry", "Tahiry", "Faneva", "Mamy", "Toky", "Hery", "Fidy",
             "Njaka", "Kanto", "Tojo", "Mickaël", "Jean", "Nantenaina", "Fenosoa",
             "Rado", "Lanto", "Mario", "Eric", "Patrick", "Sitraka", "Tafita",
             "Harilala", "Dimby", "Fabrice", "Hajanirina", "Steeve", "Joël", "Mendrika", "Yves"]
NOMS = ["Rakotoarisoa", "Rasoanaivo", "Randrianasolo", "Andriamanana", "Rakotomalala",
        "Ratsimbazafy", "Razafindrakoto", "Rabemananjara", "Andrianjaka", "Rasolofoniaina",
        "Ravelomanana", "Randriamampionona", "Rakotonirina", "Razanamahefa", "Raharison",
        "Andrianarivo", "Rasamimanana", "Rakotovao", "Ramanantsoa", "Rajaonarison",
        "Razafimahatratra", "Rafanomezantsoa", "Randrianarisoa", "Ranaivoson", "Rakotondrabe",
        "Rasolonjatovo", "Andriamihaja", "Razafiarivony", "Ravoniarisoa", "Rabary"]
QUARTIERS = ["Analakely", "Ankadifotsy", "Ambohimanarina", "Itaosy", "Ivato", "Andoharanofotsy",
             "Ampefiloha", "Anosibe", "Tanjombato", "Ambatobe", "Ankorondrano", "Isotry",
             "Ambohipo", "67 Ha", "Behoririka", "Ambanidia", "Antanimena", "Ankatso"]
MOTIFS_JUSTIF = ["Certificat médical", "Décès dans la famille", "Problème de transport",
                 "Rendez-vous administratif", "Maladie", "Cérémonie familiale"]
OBSERVATIONS = {
    "solde": ["Soldé", "Paiement intégral à l'inscription", "Tout réglé"],
    "partiel": ["Paiement par tranches", "1ère tranche versée", "Reste à régler",
                "Échéancier convenu avec les parents"],
    "faible": ["Retard de paiement", "Parents à relancer", "Promesse de versement"],
}


# ----------------------------------------------------------------------------
# Utilitaires
# ----------------------------------------------------------------------------
def telephone():
    return f"03{random.choice([2, 3, 4, 8])} {random.randint(10, 99)} {random.randint(100, 999)} {random.randint(10, 99)}"


def arrondi_quart(x):
    return round(x * 4) / 4


def jours_de_classe(n):
    jours = []
    d = datetime.now()
    while len(jours) < n:
        if d.weekday() < 5:
            jours.append(d.strftime("%d/%m/%Y"))
        d -= timedelta(days=1)
    return list(reversed(jours))


def statut_valide(nom_souhaite):
    for s in STATUTS:
        if s.lower().startswith(nom_souhaite[:3].lower()):
            return s
    return STATUTS[0]


# ----------------------------------------------------------------------------
# Réinitialisation  (cible le dossier document/ et non gen_sup/)
# ----------------------------------------------------------------------------
def reinitialiser(dossier_donnees: Path):
    """Déplace les fichiers de données de document/ dans un dossier de sauvegarde."""
    dossier_donnees.mkdir(parents=True, exist_ok=True)
    ce_script = os.path.basename(__file__)
    candidats = [
        f for f in os.listdir(dossier_donnees)
        if f.lower().endswith(EXTENSIONS_DONNEES)
        and f != ce_script
        and os.path.isfile(dossier_donnees / f)
    ]
    if not candidats:
        print(f"Aucun fichier de données trouvé dans : {dossier_donnees}")
        print("→ Rien à vider, on passe directement à la génération.")
        return True

    print(f"Fichiers de données détectés dans {dossier_donnees} :")
    for f in candidats:
        print("  -", f)
    reponse = input("\nLes déplacer dans un dossier de sauvegarde et repartir de zéro ? Tape OUI : ")
    if reponse.strip().upper() != "OUI":
        print("Annulé, rien n'a été touché.")
        return False

    sauvegarde = dossier_donnees / ("sauvegarde_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    sauvegarde.mkdir(parents=True, exist_ok=True)
    for f in candidats:
        shutil.move(str(dossier_donnees / f), str(sauvegarde / f))
    print(f"✔ {len(candidats)} fichier(s) déplacé(s) vers {sauvegarde.name}/")
    return True


# ----------------------------------------------------------------------------
# Génération
# ----------------------------------------------------------------------------
def generer_identites(nb_total):
    vus, resultat = set(), []
    tentatives = 0
    while len(resultat) < nb_total and tentatives < nb_total * 50:
        tentatives += 1
        prenom = random.choice(PRENOMS_F + PRENOMS_M)
        nom = random.choice(NOMS)
        if (nom, prenom) in vus:
            continue
        vus.add((nom, prenom))
        resultat.append((nom, prenom))
    return resultat


def inscrire_etudiants(par_classe):
    identites = generer_identites(par_classe * len(CLASSES))
    i, erreurs = 0, 0
    for classe in CLASSES:
        for _ in range(par_classe):
            nom, prenom = identites[i]
            i += 1
            try:
                Eleve(nom, prenom, classe).inscription()
            except Exception as e:
                erreurs += 1
                print(f"  ! inscription impossible ({prenom} {nom}) : {e}")
    return erreurs


def generer_notes(etudiants):
    n = 0
    profils = {}
    for num, nom, prenom, classe in etudiants:
        if random.random() < 0.05:
            continue
        niveau = random.gauss(11.2, 2.6)
        profils[num] = niveau
        notes = []
        for _ in range(6):
            v = random.gauss(niveau, 2.4)
            notes.append(max(0.0, min(20.0, arrondi_quart(v))))
        try:
            Note(int(num), nom, prenom, *notes).ajout_de_note()
            n += 1
        except Exception as e:
            print(f"  ! notes ({prenom} {nom}) : {e}")
    return n, profils


def generer_infos(etudiants):
    n = 0
    for num, nom, prenom, classe in etudiants:
        if random.random() < 0.08:
            continue
        adresse = (f"Lot {random.randint(1, 250)} "
                   f"{random.choice(['A', 'B', 'C', ''])} "
                   f"{random.choice(QUARTIERS)}, Antananarivo").replace("  ", " ")
        info = InfoEtudiant(nom, prenom, classe, adresse=adresse,
                            contact=telephone() if random.random() < 0.8 else "",
                            contact_parents=telephone())
        try:
            info.enregistrer_infos(int(num))
            n += 1
        except Exception as e:
            print(f"  ! infos ({prenom} {nom}) : {e}")
    return n


def generer_comptabilite(etudiants):
    n = 0
    for num, nom, prenom, classe in etudiants:
        if random.random() < 0.04:
            continue
        frais = CLASSES.get(classe, 450_000)
        tirage = random.random()
        if tirage < 0.40:
            paye, cat = frais, "solde"
        elif tirage < 0.85:
            paye = round(frais * random.choice([0.25, 0.33, 0.5, 0.6, 0.75]) / 5000) * 5000
            cat = "partiel"
        else:
            paye = random.choice([0, 0, 20_000, 40_000, 50_000])
            cat = "faible"
        try:
            Paiement(int(num), nom, prenom, classe, float(frais), float(paye),
                     observation=random.choice(OBSERVATIONS[cat])).enregistrer()
            n += 1
        except Exception as e:
            print(f"  ! compta ({prenom} {nom}) : {e}")
    return n


def generer_presences(etudiants_par_classe, profils):
    present = statut_valide("Présent")
    absent = statut_valide("Absent")
    retard = statut_valide("Retard")
    justifie = statut_valide("Justifié")

    assiduite = {}
    for classe, liste in etudiants_par_classe.items():
        for num, *_ in liste:
            assiduite[num] = random.choice([0.99, 0.97, 0.95, 0.93, 0.9, 0.85, 0.7])

    dates = jours_de_classe(NB_JOURS_PRESENCE)
    total = 0
    for classe, liste in etudiants_par_classe.items():
        for date in dates:
            enregistrements = []
            for num, nom, prenom, _ in liste:
                p = assiduite[num]
                r = random.random()
                justif = ""
                if r < p:
                    statut = retard if random.random() < 0.06 else present
                else:
                    if random.random() < 0.45:
                        statut, justif = justifie, random.choice(MOTIFS_JUSTIF)
                    else:
                        statut = absent
                enregistrements.append({
                    "numero": int(num), "nom": nom, "prenom": prenom,
                    "statut": statut, "justification": justif
                })
            try:
                Presence.enregistrer_lot(date, classe, enregistrements)
                total += len(enregistrements)
            except Exception as e:
                print(f"  ! présence {classe} {date} : {e}")
    return total, len(dates)


# ----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Générateur de données ScolaGest")
    parser.add_argument("--reset", action="store_true",
                        help="sauvegarde puis vide les fichiers de données avant de générer")
    parser.add_argument("--par-classe", type=int, default=16,
                        help="nombre d'étudiants par classe (défaut : 16)")
    args = parser.parse_args()

    print(f"📂 Racine du projet : {RACINE_PROJET}")
    print(f"📂 Dossier données  : {DOSSIER_DONNEES}\n")

    if args.reset and not reinitialiser(DOSSIER_DONNEES):
        sys.exit(0)

    print(f"\n➜ Inscription de {args.par_classe * len(CLASSES)} étudiants "
          f"({len(CLASSES)} classes)...")
    erreurs = inscrire_etudiants(args.par_classe)
    if erreurs:
        print(f"  {erreurs} inscription(s) en erreur.")

    etudiants_par_classe = {c: Eleve.obtenir_etudiants_par_classe(c) for c in CLASSES}
    tous = [e for liste in etudiants_par_classe.values() for e in liste]
    print(f"  ✔ {len(tous)} étudiants présents dans la base")

    print("➜ Notes...")
    nb_notes, profils = generer_notes(tous)
    print(f"  ✔ {nb_notes} étudiants avec notes")

    print("➜ Coordonnées...")
    print(f"  ✔ {generer_infos(tous)} dossiers d'informations")

    print("➜ Comptabilité...")
    print(f"  ✔ {generer_comptabilite(tous)} dossiers de paiement")

    print("➜ Présences...")
    lignes, nb_jours = generer_presences(etudiants_par_classe, profils)
    print(f"  ✔ {lignes} lignes de présence sur {nb_jours} jours")

    print("\n🎉 Terminé. Lance maintenant l'application : python main.py")


if __name__ == "__main__":
    main()