import sys
import os
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime

from generateur_pdf import GenerateurPDF
from etudiants import Eleve
from notes import Note
from infos_etudiant import InfoEtudiant
from comptabilite import Paiement
from presence import Presence, STATUTS
from pandas_base_de_donnee import lire_toutes_les_donnees


# ================== Palette de couleurs (design moderne) ==================
COULEURS = {
    "bg": "#f4f6fb",             # fond général, légèrement froid
    "sidebar": "#151a2d",        # bleu-nuit profond
    "sidebar_active": "#242b48",
    "sidebar_selected": "#3b4270",
    "accent": "#6366f1",         # indigo
    "accent_hover": "#4f46e5",
    "accent_light": "#eef0ff",
    "texte": "#1e2430",
    "texte_muet": "#6b7280",
    "blanc": "#ffffff",
    "bordure": "#e2e6f0",
    "bordure_forte": "#cfd5e6",
    "ombre": "#dde2ef",          # faux effet d'ombre (bas / droite des cartes)
    "ligne_alt": "#f8f9fd",      # lignes alternées des tableaux
    "succes": "#059669",
    "succes_bg": "#ecfdf5",
    "erreur": "#dc2626",
    "erreur_bg": "#fef2f2",
    "gris_clair": "#eef1f6",
}

POLICE = "Segoe UI"


# ================== Widgets utilitaires ==================
class CarteOmbre(tk.Frame):
    """Carte moderne : liseré fin + léger effet d'ombre en bas/à droite.
    (Tkinter ne gère ni les ombres portées ni les coins arrondis nativement.)"""
    def __init__(self, parent, padding=22, **kwargs):
        # Le fond de ce cadre sert de "ombre" visible sur 2px à droite et 3px en bas
        super().__init__(parent, bg=COULEURS["ombre"])
        self.bord = tk.Frame(self, bg=COULEURS["bordure_forte"])
        self.bord.pack(fill="both", expand=True, padx=(0, 2), pady=(0, 3))
        self.inner = ttk.Frame(self.bord, style="Card.TFrame", padding=padding)
        self.inner.pack(fill="both", expand=True, padx=1, pady=1)

    def contenu(self):
        return self.inner


class ChampAvecLabel(ttk.Frame):
    """Champ de saisie étiqueté, avec message d'erreur intégré."""
    def __init__(self, parent, label, variable, width=28, show=None):
        super().__init__(parent, style="Card.TFrame")
        ttk.Label(self, text=label, style="CardMuted.TLabel").pack(anchor="w")
        self.entry = ttk.Entry(self, textvariable=variable, width=width, show=show, font=(POLICE, 11))
        self.entry.pack(fill="x", pady=(4, 0))
        self.erreur_lbl = ttk.Label(self, text="", style="Erreur.TLabel")
        self.erreur_lbl.pack(anchor="w")

    def erreur(self, message=""):
        self.erreur_lbl.config(text=message)
        self.entry.config(style="Erreur.TEntry" if message else "TEntry")

    def focus(self):
        self.entry.focus_set()


class Badge(tk.Label):
    """Petite pastille de statut (succès / erreur / info)."""
    COULEURS_TYPE = {
        "succes": (COULEURS["succes_bg"], COULEURS["succes"]),
        "erreur": (COULEURS["erreur_bg"], COULEURS["erreur"]),
        "info": (COULEURS["accent_light"], COULEURS["accent"]),
    }

    def __init__(self, parent, texte="", type_="info"):
        bg, fg = self.COULEURS_TYPE.get(type_, self.COULEURS_TYPE["info"])
        super().__init__(parent, text=texte, bg=bg, fg=fg, font=(POLICE, 9, "bold"),
                         padx=12, pady=5, highlightthickness=1,
                         highlightbackground=fg, highlightcolor=fg)

    def maj(self, texte, type_="info"):
        bg, fg = self.COULEURS_TYPE.get(type_, self.COULEURS_TYPE["info"])
        self.config(text=texte, bg=bg, fg=fg, highlightbackground=fg, highlightcolor=fg)


# ================== Tableaux (Treeview) ==================
def configurer_tags(tree):
    """Lignes alternées pour une meilleure lisibilité."""
    tree.tag_configure("pair", background=COULEURS["blanc"])
    tree.tag_configure("impair", background=COULEURS["ligne_alt"])


def ajouter_ligne(tree, valeurs, tags=()):
    """Insère une ligne avec alternance de couleurs."""
    index = len(tree.get_children())
    tag = "pair" if index % 2 == 0 else "impair"
    return tree.insert("", tk.END, values=valeurs, tags=(tag, *tags))


def cadre_bordure(parent):
    """Cadre avec fine bordure moderne, destiné à contenir un tableau."""
    externe = tk.Frame(parent, bg=COULEURS["bordure_forte"])
    interne = tk.Frame(externe, bg=COULEURS["blanc"])
    interne.pack(fill="both", expand=True, padx=1, pady=1)
    return externe, interne


def creer_treeview_etudiants(parent):
    """Treeview standard listant des étudiants (numéro, nom, prénom, classe)."""
    externe, interne = cadre_bordure(parent)
    tree = ttk.Treeview(interne, columns=("num", "nom", "prenom", "classe"),
                        show="headings", height=6)
    entetes = {"num": "Numéro", "nom": "Nom", "prenom": "Prénom", "classe": "Classe"}
    largeurs = {"num": 80, "nom": 140, "prenom": 140, "classe": 90}
    for col, texte in entetes.items():
        tree.heading(col, text=texte)
        tree.column(col, width=largeurs[col], anchor="center" if col in ("num", "classe") else "w")
    configurer_tags(tree)
    tree.pack(side="left", fill="both", expand=True)
    scroll = ttk.Scrollbar(interne, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")
    return externe, tree


# ================== Page de base ==================
class Page(ttk.Frame):
    """Classe de base pour toutes les pages."""
    def __init__(self, parent, titre, sous_titre=""):
        super().__init__(parent, style="TFrame")
        self.titre = titre
        self.sous_titre = sous_titre
        self._construire_ui()

    def _construire_ui(self):
        header = ttk.Frame(self, style="TFrame")
        header.pack(fill='x', padx=30, pady=(25, 5))
        ttk.Label(header, text=self.titre, style="Header.TLabel").pack(anchor="w")
        if self.sous_titre:
            ttk.Label(header, text=self.sous_titre, style="SousHeader.TLabel").pack(anchor="w", pady=(2, 0))
        tk.Frame(self, bg=COULEURS["bordure_forte"], height=1).pack(fill="x", padx=30, pady=(10, 0))


class PageAvecScroll(Page):
    """Page avec zone scrollable : molette gérée globalement par Application.

    Le contenu doit être ajouté dans `self.scrollable`.
    """
    def __init__(self, parent, titre, sous_titre=""):
        super().__init__(parent, titre, sous_titre)
        self._construire_scroll()

    def _construire_scroll(self):
        conteneur = ttk.Frame(self, style="TFrame")
        conteneur.pack(fill="both", expand=True)

        canvas = tk.Canvas(conteneur, background=COULEURS["bg"], highlightthickness=0,
                           bd=0, yscrollincrement=30)
        scrollbar = ttk.Scrollbar(conteneur, orient="vertical", command=canvas.yview)
        self.scrollable = ttk.Frame(canvas, style="TFrame")

        fenetre = canvas.create_window((0, 0), window=self.scrollable, anchor="nw")

        # Zone scrollable : met à jour la région défilable quand le contenu change
        self.scrollable.bind("<Configure>",
                             lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        # Le contenu prend toute la largeur visible du canvas
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(fenetre, width=e.width))

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Référence utilisée par Application pour router la molette
        self._canvas = canvas


# ================== Accueil ==================
class AccueilPage(Page):
    def __init__(self, parent, controleur):
        super().__init__(parent, "Bienvenue 👋", "Gestion des étudiants & notes")
        self.controleur = controleur
        self._construire_contenu()

    def _construire_contenu(self):
        wrapper = ttk.Frame(self, style="TFrame")
        wrapper.pack(expand=True, fill='both', padx=30, pady=20)

        ttk.Label(wrapper, text="Que voulez-vous faire aujourd'hui ?",
                  style="TLabel", font=(POLICE, 12)).pack(anchor="w", pady=(0, 15))

        grille = ttk.Frame(wrapper, style="TFrame")
        grille.pack(fill="x")
        grille.columnconfigure((0, 1, 2), weight=1, uniform="col")

        actions = [
            ("📝", "Inscription", "Ajouter un nouvel étudiant", "inscription"),
            ("📊", "Notes", "Saisir les notes d'un étudiant", "notes"),
            ("🔍", "Recherche", "Consulter le dossier d'un étudiant", "recherche"),
            ("ℹ️", "Infos étudiant", "Modifier les coordonnées", "infos"),
        ]
        for i, (icone, titre, desc, page_key) in enumerate(actions):
            self._creer_carte_action(grille, icone, titre, desc, page_key).grid(
                row=i // 3, column=i % 3, padx=10, pady=10, sticky="nsew")

    def _creer_carte_action(self, parent, icone, titre, desc, page_key):
        carte = CarteOmbre(parent, padding=20)
        c = carte.contenu()
        ttk.Label(c, text=icone, font=(POLICE, 26), style="Card.TLabel").pack(anchor="w")
        ttk.Label(c, text=titre, font=(POLICE, 13, "bold"), style="Card.TLabel").pack(anchor="w", pady=(8, 2))
        ttk.Label(c, text=desc, font=(POLICE, 9), style="CardMuted.TLabel",
                  wraplength=180, justify="left").pack(anchor="w")
        ttk.Button(c, text="Ouvrir  →", style="Accent.TButton",
                   command=lambda: self.controleur.afficher_page(page_key)).pack(anchor="w", pady=(14, 0))
        return carte


# ================== Inscription ==================
class InscriptionPage(PageAvecScroll):
    def __init__(self, parent, controleur):
        super().__init__(parent, "Inscription d'un étudiant", "Créer un nouveau dossier étudiant")
        self.controleur = controleur
        self.var_nom = tk.StringVar()
        self.var_prenom = tk.StringVar()
        self.var_classe = tk.StringVar()
        self._construire_contenu()

    def _construire_contenu(self):
        carte = CarteOmbre(self.scrollable, padding=28)
        carte.pack(pady=25, padx=30, fill='x')
        c = carte.contenu()
        c.columnconfigure(0, weight=1)
        c.columnconfigure(1, weight=1)

        self.champ_nom = ChampAvecLabel(c, "Nom", self.var_nom)
        self.champ_nom.grid(row=0, column=0, padx=(0, 12), pady=8, sticky="ew")
        self.champ_prenom = ChampAvecLabel(c, "Prénom", self.var_prenom)
        self.champ_prenom.grid(row=0, column=1, padx=(12, 0), pady=8, sticky="ew")

        ttk.Label(c, text="Classe", style="CardMuted.TLabel").grid(row=1, column=0, sticky='w', pady=(12, 4))
        self.combo_classe = ttk.Combobox(c, textvariable=self.var_classe,
                                         values=Eleve.obtenir_classes_existantes(),
                                         state="normal", font=(POLICE, 11),
                                         postcommand=self._maj_classes)
        self.combo_classe.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        boutons = ttk.Frame(c, style="Card.TFrame")
        boutons.grid(row=3, column=0, columnspan=2, pady=(20, 5), sticky="w")
        ttk.Button(boutons, text="✔  Inscrire", style="Accent.TButton",
                   command=self._inscrire).pack(side="left")
        ttk.Button(boutons, text="Effacer", style="Secondary.TButton",
                   command=self._reinitialiser).pack(side="left", padx=(10, 0))

        self.badge = Badge(c)
        self.badge.grid(row=4, column=0, columnspan=2, pady=(15, 0), sticky="w")
        self.badge.grid_remove()

        # Ergonomie : Entrée valide le formulaire, focus initial sur "Nom"
        for widget in (self.champ_nom.entry, self.champ_prenom.entry, self.combo_classe):
            widget.bind("<Return>", lambda e: self._inscrire())
        self.champ_nom.focus()

    def _maj_classes(self):
        self.combo_classe['values'] = Eleve.obtenir_classes_existantes()

    def _reinitialiser(self):
        self.var_nom.set("")
        self.var_prenom.set("")
        self.var_classe.set("")
        self.champ_nom.erreur()
        self.champ_prenom.erreur()
        self.badge.grid_remove()
        self.champ_nom.focus()

    def _inscrire(self):
        nom = self.var_nom.get().strip()
        prenom = self.var_prenom.get().strip()
        classe = self.var_classe.get().strip()

        valide = True
        self.champ_nom.erreur()
        self.champ_prenom.erreur()
        if not nom:
            self.champ_nom.erreur("Champ requis")
            valide = False
        if not prenom:
            self.champ_prenom.erreur("Champ requis")
            valide = False
        if not classe:
            messagebox.showerror("Erreur", "La classe est obligatoire.")
            valide = False
        if not valide:
            return

        try:
            nouvel = Eleve(nom, prenom, classe)
            nouvel.inscription()
            self._reinitialiser()
            self.badge.maj(f"✔ {prenom} {nom} inscrit(e) avec succès", "succes")
            self.badge.grid()
        except Exception as e:
            self.badge.maj(f"✘ {e}", "erreur")
            self.badge.grid()


# ================== Barre de recherche réutilisable ==================
class BarreRecherche(ttk.Frame):
    """Bloc de recherche étudiant (nom/prénom) réutilisé par plusieurs pages."""
    def __init__(self, parent, on_search):
        super().__init__(parent, style="Card.TFrame")
        self.on_search = on_search
        self.var_nom = tk.StringVar()
        self.var_prenom = tk.StringVar()

        ttk.Label(self, text="🔍  Rechercher un étudiant", style="Card.TLabel",
                  font=(POLICE, 12, "bold")).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))
        ttk.Label(self, text="Nom", style="CardMuted.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8))
        ttk.Label(self, text="Prénom", style="CardMuted.TLabel").grid(row=1, column=1, sticky="w", padx=(0, 8))
        self.e1 = ttk.Entry(self, textvariable=self.var_nom, width=18, font=(POLICE, 10))
        self.e2 = ttk.Entry(self, textvariable=self.var_prenom, width=18, font=(POLICE, 10))
        self.e1.grid(row=2, column=0, padx=(0, 8), sticky="ew")
        self.e2.grid(row=2, column=1, padx=(0, 8), sticky="ew")
        ttk.Button(self, text="Rechercher", style="Accent.TButton",
                   command=self._rechercher).grid(row=2, column=2)
        for w in (self.e1, self.e2):
            w.bind("<Return>", lambda e: self._rechercher())
        self.columnconfigure((0, 1), weight=1)

    def _rechercher(self):
        nom = self.var_nom.get().strip()
        prenom = self.var_prenom.get().strip()
        if not nom and not prenom:
            messagebox.showwarning("Champs vides", "Entrez au moins un nom ou un prénom.")
            return
        self.on_search(nom, prenom)

    def focus(self):
        self.e1.focus_set()


# ================== Ajout de notes ==================
class NotesPage(PageAvecScroll):
    MATIERES = ["Math", "PC", "HG", "Malagasy", "Français", "Philo"]

    def __init__(self, parent, controleur):
        super().__init__(parent, "Ajout de notes", "Sélectionnez un étudiant puis saisissez ses notes (/20)")
        self.controleur = controleur
        self.numero_courant = None
        self.entries_notes = []
        self._construire_contenu()

    def _construire_contenu(self):
        carte_recherche = CarteOmbre(self.scrollable, padding=20)
        carte_recherche.pack(pady=15, padx=30, fill='x')
        self.recherche = BarreRecherche(carte_recherche.contenu(), self._rechercher)
        self.recherche.pack(fill="x")

        frame_res, self.tree_etudiants = creer_treeview_etudiants(self.scrollable)
        frame_res.pack(pady=(5, 10), padx=30, fill='x')
        self.tree_etudiants.bind("<Double-1>", lambda e: self._selectionner())

        actions_res = ttk.Frame(self.scrollable, style="TFrame")
        actions_res.pack(padx=30, fill="x")
        ttk.Button(actions_res, text="Sélectionner →", style="Accent.TButton",
                   command=self._selectionner).pack(anchor="e", pady=(0, 15))

        carte_notes = CarteOmbre(self.scrollable, padding=22)
        carte_notes.pack(pady=(0, 25), padx=30, fill='both', expand=True)
        c = carte_notes.contenu()

        self.label_selection = ttk.Label(c, text="Aucun étudiant sélectionné",
                                         style="CardMuted.TLabel", font=(POLICE, 10, "bold"))
        self.label_selection.grid(row=0, column=0, columnspan=4, pady=(0, 15), sticky='w')

        self.vars_notes = [tk.StringVar() for _ in range(6)]
        vcmd = (self.register(self._valider_note), "%P")
        for i, (mat, var) in enumerate(zip(self.MATIERES, self.vars_notes)):
            row, col = divmod(i, 2)
            bloc = ttk.Frame(c, style="Card.TFrame")
            bloc.grid(row=row + 1, column=col, padx=10, pady=8, sticky="ew")
            ttk.Label(bloc, text=mat, style="CardMuted.TLabel").pack(anchor="w")
            entry = ttk.Entry(bloc, textvariable=var, width=12, state='disabled',
                              font=(POLICE, 11), validate="key", validatecommand=vcmd)
            entry.pack(fill="x", pady=(3, 0))
            self.entries_notes.append(entry)
        c.columnconfigure((0, 1), weight=1)

        boutons = ttk.Frame(c, style="Card.TFrame")
        boutons.grid(row=5, column=0, columnspan=4, pady=(20, 5), sticky="w")
        self.btn_ajouter = ttk.Button(boutons, text="💾  Enregistrer les notes", style="Accent.TButton",
                                      state='disabled', command=self._ajouter)
        self.btn_ajouter.pack(side="left")

        self.badge = Badge(c)
        self.badge.grid(row=6, column=0, columnspan=4, pady=(15, 0), sticky="w")
        self.badge.grid_remove()

    @staticmethod
    def _valider_note(texte_propose):
        """Autorise uniquement un nombre décimal entre 0 et 20 (validation en direct)."""
        if texte_propose in ("", "."):
            return True
        try:
            valeur = float(texte_propose)
        except ValueError:
            return False
        return 0 <= valeur <= 20

    def _rechercher(self, nom, prenom):
        for item in self.tree_etudiants.get_children():
            self.tree_etudiants.delete(item)
        resultats = Eleve.rechercher_par_nom_prenom(nom, prenom)
        if not resultats:
            messagebox.showinfo("Aucun résultat", "Aucun étudiant trouvé.")
            return
        for num, n, p, c in resultats:
            ajouter_ligne(self.tree_etudiants, (num, n, p, c))

    def _selectionner(self):
        sel = self.tree_etudiants.selection()
        if not sel:
            messagebox.showwarning("Sélection", "Sélectionnez un étudiant dans la liste.")
            return
        num, nom, prenom, classe = self.tree_etudiants.item(sel[0])['values']
        self.numero_courant = int(num)
        self.label_selection.config(text=f"📌  {prenom} {nom}  •  {classe}  •  n°{num}",
                                    style="Card.TLabel")
        for entry in self.entries_notes:
            entry.config(state='normal')
        self.btn_ajouter.config(state='normal')
        self.entries_notes[0].focus_set()

    def _ajouter(self):
        if self.numero_courant is None:
            return
        notes = []
        for i, var in enumerate(self.vars_notes):
            try:
                note = float(var.get().strip())
                if note < 0 or note > 20:
                    raise ValueError
                notes.append(note)
            except ValueError:
                messagebox.showerror("Erreur", f"Note invalide pour {self.MATIERES[i]} (attendu : 0-20).")
                self.entries_notes[i].focus_set()
                return
        etudiant = Eleve.etudiant(self.numero_courant)
        nouvelle = Note(self.numero_courant, etudiant.nom, etudiant.prenom, *notes)
        try:
            nouvelle.ajout_de_note()
            for var in self.vars_notes:
                var.set("")
            for entry in self.entries_notes:
                entry.config(state='disabled')
            self.btn_ajouter.config(state='disabled')
            self.label_selection.config(text="Aucun étudiant sélectionné", style="CardMuted.TLabel")
            self.numero_courant = None
            self.badge.maj("✔ Notes enregistrées avec succès", "succes")
            self.badge.grid()
        except Exception as e:
            self.badge.maj(f"✘ {e}", "erreur")
            self.badge.grid()


# ================== Recherche (dossier étudiant) ==================
class RecherchePage(PageAvecScroll):
    def __init__(self, parent, controleur):
        super().__init__(parent, "Recherche d'étudiant", "Consultez les notes et informations d'un étudiant")
        self.controleur = controleur
        self._construire_contenu()

    def _construire_contenu(self):
        carte_recherche = CarteOmbre(self.scrollable, padding=20)
        carte_recherche.pack(pady=15, padx=30, fill='x')
        self.recherche = BarreRecherche(carte_recherche.contenu(), self._rechercher)
        self.recherche.pack(fill="x")

        frame_res, self.tree_etudiants = creer_treeview_etudiants(self.scrollable)
        frame_res.pack(pady=(5, 10), padx=30, fill='x')
        self.tree_etudiants.bind("<Double-1>", lambda e: self._selectionner())

        ttk.Button(self.scrollable, text="Sélectionner →", style="Accent.TButton",
                   command=self._selectionner).pack(padx=30, anchor="e", pady=(0, 15))

        carte_details = CarteOmbre(self.scrollable, padding=22)
        carte_details.pack(pady=(0, 25), padx=30, fill='both', expand=True)
        c = carte_details.contenu()

        self.label_etudiant = ttk.Label(c, text="Aucun étudiant sélectionné",
                                        style="CardMuted.TLabel", font=(POLICE, 10, "bold"))
        self.label_etudiant.pack(anchor='w', pady=(0, 15))

        deux_colonnes = ttk.Frame(c, style="Card.TFrame")
        deux_colonnes.pack(fill="both", expand=True)
        deux_colonnes.columnconfigure((0, 1), weight=1)

        bloc_notes = ttk.Frame(deux_colonnes, style="Card.TFrame")
        bloc_notes.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        ttk.Label(bloc_notes, text="📊  Notes", style="Card.TLabel",
                  font=(POLICE, 11, "bold")).pack(anchor="w", pady=(0, 8))
        cadre_notes, interne_notes = cadre_bordure(bloc_notes)
        cadre_notes.pack(fill="both", expand=True)
        self.tree_notes = ttk.Treeview(interne_notes, columns=("matiere", "note"),
                                       show="headings", height=6)
        self.tree_notes.heading("matiere", text="Matière")
        self.tree_notes.heading("note", text="Note /20")
        self.tree_notes.column("matiere", width=140, anchor='w')
        self.tree_notes.column("note", width=80, anchor='center')
        configurer_tags(self.tree_notes)
        self.tree_notes.pack(fill="both", expand=True)

        bloc_infos = ttk.Frame(deux_colonnes, style="Card.TFrame")
        bloc_infos.grid(row=0, column=1, sticky="nsew")
        ttk.Label(bloc_infos, text="ℹ️  Coordonnées", style="Card.TLabel",
                  font=(POLICE, 11, "bold")).pack(anchor="w", pady=(0, 8))
        self.label_infos = ttk.Label(bloc_infos, text="", style="CardMuted.TLabel", justify="left")
        self.label_infos.pack(anchor='w')

    def _rechercher(self, nom, prenom):
        for item in self.tree_etudiants.get_children():
            self.tree_etudiants.delete(item)
        resultats = Eleve.rechercher_par_nom_prenom(nom, prenom)
        if not resultats:
            messagebox.showinfo("Aucun résultat", "Aucun étudiant trouvé.")
            return
        for num, n, p, c in resultats:
            ajouter_ligne(self.tree_etudiants, (num, n, p, c))

    def _selectionner(self):
        sel = self.tree_etudiants.selection()
        if not sel:
            messagebox.showwarning("Sélection", "Sélectionnez un étudiant.")
            return
        num, nom, prenom, classe = self.tree_etudiants.item(sel[0])['values']
        self.label_etudiant.config(text=f"👤  {prenom} {nom}  •  {classe}  •  n°{num}", style="Card.TLabel")

        for row in self.tree_notes.get_children():
            self.tree_notes.delete(row)
        etudiant = Eleve.etudiant(int(num))
        note_obj = Note.afficher_les_notes_d_un_etudiant(int(num), etudiant)
        if note_obj:
            notes_data = [
                ("Math", note_obj.note_math), ("PC", note_obj.note_pc),
                ("HG", note_obj.note_hg), ("Malagasy", note_obj.note_malagasy),
                ("Français", note_obj.note_francais), ("Philo", note_obj.note_philo),
            ]
            for matiere, note in notes_data:
                ajouter_ligne(self.tree_notes, (matiere, note))
        else:
            ajouter_ligne(self.tree_notes, ("Aucune note", "—"))

        infos = InfoEtudiant.charger_infos(int(num))
        if infos:
            self.label_infos.config(
                text=f"Adresse :\n{infos.adresse}\n\nContact :\n{infos.contact}\n\nParents :\n{infos.contact_parents}")
        else:
            self.label_infos.config(text="Aucune information complémentaire enregistrée.")


# ================== Infos étudiant ==================
class InfosPage(PageAvecScroll):
    def __init__(self, parent, controleur):
        super().__init__(parent, "Informations étudiant", "Adresse et contacts de l'étudiant")
        self.controleur = controleur
        self.numero_courant = None
        self._construire_contenu()

    def _construire_contenu(self):
        carte_recherche = CarteOmbre(self.scrollable, padding=20)
        carte_recherche.pack(pady=15, padx=30, fill='x')
        self.recherche = BarreRecherche(carte_recherche.contenu(), self._rechercher)
        self.recherche.pack(fill="x")

        frame_res, self.tree_etudiants = creer_treeview_etudiants(self.scrollable)
        frame_res.pack(pady=(5, 10), padx=30, fill='x')
        self.tree_etudiants.bind("<Double-1>", lambda e: self._selectionner())

        ttk.Button(self.scrollable, text="Sélectionner →", style="Accent.TButton",
                   command=self._selectionner).pack(padx=30, anchor="e", pady=(0, 15))

        carte_infos = CarteOmbre(self.scrollable, padding=22)
        carte_infos.pack(pady=(0, 25), padx=30, fill='both', expand=True)
        c = carte_infos.contenu()
        c.columnconfigure(0, weight=1)

        self.label_etudiant = ttk.Label(c, text="Aucun étudiant sélectionné",
                                        style="CardMuted.TLabel", font=(POLICE, 10, "bold"))
        self.label_etudiant.grid(row=0, column=0, pady=(0, 15), sticky='w')

        self.var_adresse = tk.StringVar()
        self.var_contact = tk.StringVar()
        self.var_contact_parents = tk.StringVar()
        self.champ_adresse = ChampAvecLabel(c, "Adresse", self.var_adresse, width=45)
        self.champ_adresse.grid(row=1, column=0, sticky="ew", pady=6)
        self.champ_contact = ChampAvecLabel(c, "Contact", self.var_contact, width=45)
        self.champ_contact.grid(row=2, column=0, sticky="ew", pady=6)
        self.champ_parents = ChampAvecLabel(c, "Contact parents", self.var_contact_parents, width=45)
        self.champ_parents.grid(row=3, column=0, sticky="ew", pady=6)

        self.btn_enregistrer = ttk.Button(c, text="💾  Enregistrer", style="Accent.TButton",
                                          state='disabled', command=self._enregistrer)
        self.btn_enregistrer.grid(row=4, column=0, pady=(18, 5), sticky="w")

        self.badge = Badge(c)
        self.badge.grid(row=5, column=0, pady=(10, 0), sticky="w")
        self.badge.grid_remove()

    def _rechercher(self, nom, prenom):
        for item in self.tree_etudiants.get_children():
            self.tree_etudiants.delete(item)
        resultats = Eleve.rechercher_par_nom_prenom(nom, prenom)
        if not resultats:
            messagebox.showinfo("Aucun résultat", "Aucun étudiant trouvé.")
            return
        for num, n, p, c in resultats:
            ajouter_ligne(self.tree_etudiants, (num, n, p, c))

    def _selectionner(self):
        sel = self.tree_etudiants.selection()
        if not sel:
            messagebox.showwarning("Sélection", "Sélectionnez un étudiant.")
            return
        num, nom, prenom, classe = self.tree_etudiants.item(sel[0])['values']
        self.numero_courant = int(num)
        self.label_etudiant.config(text=f"👤  {prenom} {nom}  •  {classe}  •  n°{num}", style="Card.TLabel")
        infos = InfoEtudiant.charger_infos(int(num))
        self.var_adresse.set(infos.adresse if infos else "")
        self.var_contact.set(infos.contact if infos else "")
        self.var_contact_parents.set(infos.contact_parents if infos else "")
        self.btn_enregistrer.config(state='normal')
        self.badge.grid_remove()
        self.champ_adresse.focus()

    def _enregistrer(self):
        if self.numero_courant is None:
            return
        etudiant = Eleve.etudiant(self.numero_courant)
        info = InfoEtudiant(etudiant.nom, etudiant.prenom, etudiant.classe,
                            adresse=self.var_adresse.get().strip(),
                            contact=self.var_contact.get().strip(),
                            contact_parents=self.var_contact_parents.get().strip())
        try:
            info.enregistrer_infos(self.numero_courant)
            self.badge.maj("✔ Informations enregistrées", "succes")
            self.badge.grid()
            self.btn_enregistrer.config(state='disabled')
            self.numero_courant = None
        except Exception as e:
            self.badge.maj(f"✘ {e}", "erreur")
            self.badge.grid()


# ================== Comptabilité ==================
class ComptabilitePage(PageAvecScroll):
    def __init__(self, parent, controleur):
        super().__init__(parent, "Comptabilité", "Suivi des frais scolaires et versements")
        self.controleur = controleur
        self.numero_courant = None
        self._construire_contenu()

    def _construire_contenu(self):
        carte_recherche = CarteOmbre(self.scrollable, padding=20)
        carte_recherche.pack(pady=15, padx=30, fill='x')
        self.recherche = BarreRecherche(carte_recherche.contenu(), self._rechercher)
        self.recherche.pack(fill="x")

        frame_res, self.tree_etudiants = creer_treeview_etudiants(self.scrollable)
        frame_res.pack(pady=(5, 10), padx=30, fill='x')
        self.tree_etudiants.bind("<Double-1>", lambda e: self._selectionner())

        ttk.Button(self.scrollable, text="Sélectionner →", style="Accent.TButton",
                   command=self._selectionner).pack(padx=30, anchor="e", pady=(0, 15))

        carte = CarteOmbre(self.scrollable, padding=22)
        carte.pack(pady=(0, 25), padx=30, fill='both', expand=True)
        c = carte.contenu()
        c.columnconfigure((0, 1), weight=1)

        self.label_etudiant = ttk.Label(c, text="Aucun étudiant sélectionné",
                                        style="CardMuted.TLabel", font=(POLICE, 10, "bold"))
        self.label_etudiant.grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky='w')

        self.var_frais = tk.StringVar()
        self.var_paye = tk.StringVar()
        self.var_observation = tk.StringVar()

        ttk.Label(c, text="Frais total (Ar)", style="CardMuted.TLabel").grid(row=1, column=0, sticky='w', pady=(4, 0))
        self.entry_frais = ttk.Entry(c, textvariable=self.var_frais, font=(POLICE, 11))
        self.entry_frais.grid(row=2, column=0, sticky='ew', padx=(0, 8), pady=(2, 10))

        ttk.Label(c, text="Montant déjà payé (Ar)", style="CardMuted.TLabel").grid(row=1, column=1, sticky='w', pady=(4, 0))
        self.entry_paye = ttk.Entry(c, textvariable=self.var_paye, font=(POLICE, 11))
        self.entry_paye.grid(row=2, column=1, sticky='ew', padx=(8, 0), pady=(2, 10))

        ttk.Label(c, text="Observation", style="CardMuted.TLabel").grid(row=3, column=0, columnspan=2, sticky='w', pady=(4, 0))
        self.entry_obs = ttk.Entry(c, textvariable=self.var_observation, font=(POLICE, 11))
        self.entry_obs.grid(row=4, column=0, columnspan=2, sticky='ew', pady=(2, 15))

        boutons = ttk.Frame(c, style="Card.TFrame")
        boutons.grid(row=5, column=0, columnspan=2, sticky='w')
        self.btn_enregistrer = ttk.Button(boutons, text="💾  Enregistrer le dossier",
                                          style="Accent.TButton", state='disabled',
                                          command=self._enregistrer)
        self.btn_enregistrer.pack(side="left")
        self.btn_verser = ttk.Button(boutons, text="➕  Ajouter un versement",
                                     style="Secondary.TButton", state='disabled',
                                     command=self._verser)
        self.btn_verser.pack(side="left", padx=(10, 0))

        self.label_resume = ttk.Label(c, text="", style="Card.TLabel",
                                      font=(POLICE, 11, "bold"), justify="left")
        self.label_resume.grid(row=6, column=0, columnspan=2, sticky='w', pady=(15, 0))

        self.badge = Badge(c)
        self.badge.grid(row=7, column=0, columnspan=2, pady=(10, 0), sticky="w")
        self.badge.grid_remove()

    def _rechercher(self, nom, prenom):
        for item in self.tree_etudiants.get_children():
            self.tree_etudiants.delete(item)
        resultats = Eleve.rechercher_par_nom_prenom(nom, prenom)
        if not resultats:
            messagebox.showinfo("Aucun résultat", "Aucun étudiant trouvé.")
            return
        for num, n, p, cl in resultats:
            ajouter_ligne(self.tree_etudiants, (num, n, p, cl))

    def _selectionner(self):
        sel = self.tree_etudiants.selection()
        if not sel:
            messagebox.showwarning("Sélection", "Sélectionnez un étudiant.")
            return
        num, nom, prenom, classe = self.tree_etudiants.item(sel[0])['values']
        self.numero_courant = int(num)
        self.label_etudiant.config(
            text=f"👤  {prenom} {nom}  •  {classe}  •  n°{num}",
            style="Card.TLabel"
        )
        p = Paiement.charger(self.numero_courant)
        if p:
            self.var_frais.set(str(p.frais_total))
            self.var_paye.set(str(p.montant_paye))
            self.var_observation.set(p.observation)
            self.label_resume.config(
                text=f"Reste à payer : {p.reste:,.0f} Ar     •     Statut : {p.statut}"
            )
            self.btn_verser.config(state='normal')
        else:
            self.var_frais.set("")
            self.var_paye.set("")
            self.var_observation.set("")
            self.label_resume.config(text="Aucun dossier — créez-en un ci-dessous.")
            self.btn_verser.config(state='disabled')

        self.btn_enregistrer.config(state='normal')
        self.badge.grid_remove()
        self.entry_frais.focus_set()

    def _enregistrer(self):
        if self.numero_courant is None:
            return
        try:
            frais = float(self.var_frais.get().strip() or 0)
            paye = float(self.var_paye.get().strip() or 0)
            if frais <= 0:
                raise ValueError("Le montant des frais doit être supérieur à 0.")
            if paye < 0:
                raise ValueError("Le montant payé ne peut pas être négatif.")
        except ValueError as e:
            messagebox.showerror("Erreur de saisie", str(e))
            return

        etudiant = Eleve.etudiant(self.numero_courant)
        p = Paiement(
            self.numero_courant, etudiant.nom, etudiant.prenom, etudiant.classe,
            frais, paye, observation=self.var_observation.get().strip()
        )
        try:
            p.enregistrer()
            self.label_resume.config(
                text=f"Reste à payer : {p.reste:,.0f} Ar     •     Statut : {p.statut}"
            )
            self.btn_verser.config(state='normal')
            self.badge.maj(f"✔ Dossier enregistré — {p.statut}", "succes")
            self.badge.grid()
        except Exception as e:
            self.badge.maj(f"✘ {e}", "erreur")
            self.badge.grid()

    def _verser(self):
        if self.numero_courant is None:
            return
        montant = simpledialog.askfloat(
            "Nouveau versement",
            "Montant du versement (Ar) :",
            parent=self, minvalue=1
        )
        if not montant:
            return
        try:
            p = Paiement.ajouter_versement(self.numero_courant, montant)
            self.var_paye.set(str(p.montant_paye))
            self.var_observation.set(p.observation)
            self.label_resume.config(
                text=f"Reste à payer : {p.reste:,.0f} Ar     •     Statut : {p.statut}"
            )
            self.badge.maj(f"✔ Versement de {montant:,.0f} Ar enregistré", "succes")
            self.badge.grid()
        except Exception as e:
            self.badge.maj(f"✘ {e}", "erreur")
            self.badge.grid()


# ================== Présence ==================
class PresencePage(PageAvecScroll):
    # Couleurs de fond des lignes selon le statut
    TAGS_STATUT = {
        "Absent": "#fef2f2",
        "Retard": "#fffbeb",
        "Justifié": "#eff6ff",
    }

    def __init__(self, parent, controleur):
        super().__init__(parent, "Présence", "Feuille d'appel par classe et par date")
        self.controleur = controleur
        self._construire_contenu()

    def _construire_contenu(self):
        # ----- Carte de sélection (classe + date) -----
        carte = CarteOmbre(self.scrollable, padding=22)
        carte.pack(pady=15, padx=30, fill='x')
        c = carte.contenu()
        c.columnconfigure((0, 1), weight=1)

        ttk.Label(c, text="Classe", style="CardMuted.TLabel").grid(row=0, column=0, sticky='w')
        self.var_classe = tk.StringVar()
        self.combo_classe = ttk.Combobox(
            c, textvariable=self.var_classe,
            values=Eleve.obtenir_classes_existantes(),
            state="readonly", font=(POLICE, 11),
            postcommand=lambda: self.combo_classe.config(
                values=Eleve.obtenir_classes_existantes())
        )
        self.combo_classe.grid(row=1, column=0, sticky='ew', padx=(0, 8), pady=(2, 10))

        ttk.Label(c, text="Date (JJ/MM/AAAA)", style="CardMuted.TLabel").grid(row=0, column=1, sticky='w')
        self.var_date = tk.StringVar(value=datetime.now().strftime("%d/%m/%Y"))
        self.entry_date = ttk.Entry(c, textvariable=self.var_date, font=(POLICE, 11))
        self.entry_date.grid(row=1, column=1, sticky='ew', padx=(8, 0), pady=(2, 10))

        boutons_top = ttk.Frame(c, style="Card.TFrame")
        boutons_top.grid(row=2, column=0, columnspan=2, sticky='w', pady=(5, 0))
        ttk.Button(boutons_top, text="🔄  Charger la liste",
                   style="Accent.TButton",
                   command=self._charger_liste).pack(side="left")
        ttk.Button(boutons_top, text="✔  Tout marquer présent",
                   style="Secondary.TButton",
                   command=self._tout_present).pack(side="left", padx=(10, 0))
        ttk.Button(boutons_top, text="✏️  Modifier la justification",
                   style="Secondary.TButton",
                   command=self._modifier_justification).pack(side="left", padx=(10, 0))

        # ----- Tableau de présence -----
        carte_tab = CarteOmbre(self.scrollable, padding=18)
        carte_tab.pack(pady=(0, 10), padx=30, fill='both', expand=True)
        ct = carte_tab.contenu()

        self.label_entete = ttk.Label(
            ct, text="Sélectionnez une classe et une date, puis cliquez sur Charger la liste.",
            style="CardMuted.TLabel", font=(POLICE, 10, "bold"))
        self.label_entete.pack(anchor='w', pady=(0, 10))

        cadre, interne = cadre_bordure(ct)
        cadre.pack(fill="both", expand=True)
        colonnes = ("num", "nom", "prenom", "statut", "justif")
        self.tree = ttk.Treeview(interne, columns=colonnes, show="headings", height=12)
        for col, txt, w in [
            ("num", "Numéro", 70), ("nom", "Nom", 150), ("prenom", "Prénom", 150),
            ("statut", "Statut", 110), ("justif", "Justification", 240),
        ]:
            self.tree.heading(col, text=txt)
            self.tree.column(col, width=w, anchor="center" if col in ("num", "statut") else "w")
        for statut, couleur in self.TAGS_STATUT.items():
            self.tree.tag_configure(f"st_{statut}", background=couleur)
        self.tree.pack(fill="both", expand=True)

        # Double-clic : cycle Présent → Absent → Retard → Justifié → Présent
        self.tree.bind("<Double-1>", self._cycle_statut)

        # ----- Boutons du bas -----
        bas = ttk.Frame(self.scrollable, style="TFrame")
        bas.pack(padx=30, fill='x', pady=(0, 15))
        ttk.Label(bas,
                  text="💡 Double-cliquez sur une ligne pour changer le statut. "
                       "Pour modifier la justification, sélectionnez la ligne puis cliquez sur ✏️.",
                  style="SousHeader.TLabel", wraplength=560, justify="left").pack(side="left")
        self.btn_save = ttk.Button(bas, text="💾  Enregistrer la feuille",
                                   style="Accent.TButton", state='disabled',
                                   command=self._enregistrer)
        self.btn_save.pack(side="right")

        self.badge = Badge(self.scrollable)
        self.badge.pack(padx=30, anchor='w', pady=(0, 20))
        self.badge.pack_forget()

    # ---------- Helpers ----------
    def _tags_statut(self, statut):
        return (f"st_{statut}",) if statut in self.TAGS_STATUT else ()

    def _maj_ligne(self, item, vals):
        self.tree.item(item, values=vals, tags=self._tags_statut(vals[3]))

    def _charger_liste(self):
        classe = self.var_classe.get().strip()
        date = self.var_date.get().strip()
        if not classe:
            messagebox.showwarning("Classe", "Sélectionnez une classe.")
            return
        if not date:
            messagebox.showwarning("Date", "Saisissez une date.")
            return
        try:
            datetime.strptime(date, "%d/%m/%Y")
        except ValueError:
            messagebox.showerror("Date invalide", "Format attendu : JJ/MM/AAAA")
            return

        etudiants = Eleve.obtenir_etudiants_par_classe(classe)
        if not etudiants:
            messagebox.showinfo("Aucun étudiant", f"Aucun étudiant dans la classe {classe}.")
            return

        deja_statut = Presence.charger_pour_date_classe(date, classe)
        deja_justif = Presence.charger_justifications_pour_date_classe(date, classe)

        for item in self.tree.get_children():
            self.tree.delete(item)

        for num, nom, prenom, cl in etudiants:
            statut = deja_statut.get(int(num), "Présent")
            justif = deja_justif.get(int(num), "")
            self.tree.insert("", tk.END, values=(num, nom, prenom, statut, justif),
                             tags=self._tags_statut(statut))

        self.label_entete.config(
            text=f"📋  {classe}  •  {date}  •  {len(etudiants)} étudiant(s)")
        self.btn_save.config(state='normal')
        self.badge.maj("Liste chargée", "info")
        self.badge.pack(padx=30, anchor='w', pady=(0, 20))

    def _tout_present(self):
        for item in self.tree.get_children():
            vals = list(self.tree.item(item, "values"))
            vals[3] = "Présent"
            self._maj_ligne(item, vals)

    def _cycle_statut(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        vals = list(self.tree.item(item, "values"))
        actuel = vals[3]
        try:
            i = STATUTS.index(actuel)
        except ValueError:
            i = 0
        nouveau = STATUTS[(i + 1) % len(STATUTS)]
        vals[3] = nouveau

        if nouveau == "Justifié":
            motif = simpledialog.askstring(
                "Justification",
                f"Motif pour {vals[2]} {vals[1]} :",
                parent=self, initialvalue=vals[4] or ""
            )
            vals[4] = motif if motif else ""
        elif nouveau == "Présent":
            vals[4] = ""

        self._maj_ligne(item, vals)

    def _modifier_justification(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sélection", "Sélectionnez d'abord une ligne.")
            return
        item = sel[0]
        vals = list(self.tree.item(item, "values"))
        motif = simpledialog.askstring(
            "Justification",
            f"Motif pour {vals[2]} {vals[1]} :",
            parent=self, initialvalue=vals[4] or ""
        )
        if motif is None:
            return
        vals[4] = motif.strip()
        if vals[4] and vals[3] == "Absent":
            vals[3] = "Justifié"
        self._maj_ligne(item, vals)

    def _enregistrer(self):
        classe = self.var_classe.get().strip()
        date = self.var_date.get().strip()
        if not classe or not date:
            return
        lignes = self.tree.get_children()
        if not lignes:
            messagebox.showwarning("Vide", "Aucune ligne à enregistrer.")
            return

        enregistrements = []
        for item in lignes:
            num, nom, prenom, statut, justif = self.tree.item(item, "values")
            enregistrements.append({
                "numero": int(num), "nom": nom, "prenom": prenom,
                "statut": statut, "justification": justif,
            })

        try:
            Presence.enregistrer_lot(date, classe, enregistrements)
            self.badge.maj(f"✔ {len(enregistrements)} présences enregistrées", "succes")
            self.badge.pack(padx=30, anchor='w', pady=(0, 20))
        except Exception as e:
            self.badge.maj(f"✘ {e}", "erreur")
            self.badge.pack(padx=30, anchor='w', pady=(0, 20))


# ================== Tableau de bord ==================
class DashboardPage(PageAvecScroll):
    def __init__(self, parent, controleur):
        super().__init__(parent, "Tableau de bord", "Vue d'ensemble de l'établissement")
        self.controleur = controleur
        self._construire_contenu()

    def _construire_contenu(self):
        barre = ttk.Frame(self.scrollable, style="TFrame")
        barre.pack(fill='x', padx=30, pady=(15, 0))
        ttk.Button(barre, text="🔄  Rafraîchir", style="Accent.TButton",
                   command=self._charger).pack(side="right")

        self.zone = ttk.Frame(self.scrollable, style="TFrame")
        self.zone.pack(fill="both", expand=True, padx=30, pady=(10, 25))

        self._charger()

    def _vider_zone(self):
        for w in self.zone.winfo_children():
            w.destroy()

    def _carte_stat(self, parent, icone, titre, valeur, sous_texte="", couleur=None):
        carte = CarteOmbre(parent, padding=18)
        c = carte.contenu()
        ttk.Label(c, text=icone, font=(POLICE, 22), style="Card.TLabel").pack(anchor='w')
        ttk.Label(c, text=titre, font=(POLICE, 9), style="CardMuted.TLabel").pack(anchor='w', pady=(6, 0))
        couleur = couleur or COULEURS["accent"]
        lbl_val = tk.Label(c, text=valeur, font=(POLICE, 20, "bold"),
                           bg=COULEURS["blanc"], fg=couleur)
        lbl_val.pack(anchor='w', pady=(2, 0))
        if sous_texte:
            ttk.Label(c, text=sous_texte, font=(POLICE, 8),
                      style="CardMuted.TLabel").pack(anchor='w')
        return carte

    def _carte_liste(self, parent, titre, lignes):
        carte = CarteOmbre(parent, padding=18)
        c = carte.contenu()
        ttk.Label(c, text=titre, font=(POLICE, 12, "bold"),
                  style="Card.TLabel").pack(anchor='w', pady=(0, 10))
        if not lignes:
            ttk.Label(c, text="Aucune donnée", style="CardMuted.TLabel").pack(anchor='w')
            return carte
        for gauche, droite in lignes:
            ligne = ttk.Frame(c, style="Card.TFrame")
            ligne.pack(fill='x', pady=2)
            ttk.Label(ligne, text=gauche, style="Card.TLabel",
                      font=(POLICE, 10)).pack(side='left')
            ttk.Label(ligne, text=droite, style="Card.TLabel",
                      font=(POLICE, 10, "bold")).pack(side='right')
        return carte

    def _charger(self):
        self._vider_zone()
        data = lire_toutes_les_donnees()
        df_et = data["etudiants"]
        df_no = data["notes"]
        df_co = data["comptabilite"]
        df_pr = data["presences"]

        # ---------- 1. Statistiques étudiants ----------
        nb_etudiants = len(df_et) if not df_et.empty else 0
        nb_classes = df_et["Classe"].nunique() if not df_et.empty and "Classe" in df_et.columns else 0
        repartition = []
        if not df_et.empty and "Classe" in df_et.columns:
            vc = df_et["Classe"].value_counts().sort_index()
            repartition = [(str(cl), f"{n} étudiant(s)") for cl, n in vc.items()]

        # ---------- 2. Statistiques comptabilité ----------
        attendu = 0.0
        percu = 0.0
        reste = 0.0
        nb_soldes = 0
        if not df_co.empty:
            attendu = float(pd.to_numeric(df_co.get("Frais_Total", 0), errors="coerce").fillna(0).sum())
            percu = float(pd.to_numeric(df_co.get("Montant_Paye", 0), errors="coerce").fillna(0).sum())
            reste = max(0.0, attendu - percu)
            if "Statut" in df_co.columns:
                nb_soldes = int((df_co["Statut"].astype(str) == "Soldé").sum())
        taux_recouv = round(percu / attendu * 100, 1) if attendu else 0.0

        # ---------- 3. Statistiques présence ----------
        taux_presence_global = 0.0
        top_assidus = []
        if not df_pr.empty:
            total = len(df_pr)
            pres = df_pr["Statut"].isin(["Présent", "Retard", "Justifié"]).sum()
            taux_presence_global = round(pres / total * 100, 1) if total else 0.0
            stats = []
            for num, g in df_pr.groupby("Numero"):
                t = len(g)
                p = g["Statut"].isin(["Présent", "Retard", "Justifié"]).sum()
                taux = round(p / t * 100, 1) if t else 0.0
                ligne = g.iloc[0]
                stats.append((ligne.get("Nom", ""), ligne.get("Prenom", ""), taux))
            stats.sort(key=lambda x: x[2], reverse=True)
            top_assidus = [(f"{p} {n}", f"{t}%") for n, p, t in stats[:3]]

        # ---------- 4. Moyenne par classe ----------
        moyennes = []
        if not df_no.empty and not df_et.empty and "Classe" in df_et.columns:
            try:
                fusion = pd.merge(
                    df_no,
                    df_et[["Numero", "Classe"]],
                    on="Numero", how="left"
                )
                matieres = [c for c in ["Math", "PC", "HG", "Malagasy", "Francais", "Philo"]
                            if c in fusion.columns]
                if matieres:
                    fusion["_moy"] = fusion[matieres].apply(
                        lambda r: pd.to_numeric(r, errors="coerce").mean(), axis=1
                    )
                    grp = fusion.groupby("Classe")["_moy"].mean().round(2)
                    moyennes = [(str(cl), f"{v}/20") for cl, v in grp.items()]
            except Exception:
                pass

        # ============ AFFICHAGE ============
        row1 = ttk.Frame(self.zone, style="TFrame")
        row1.pack(fill='x', pady=(0, 12))
        row1.columnconfigure((0, 1, 2, 3), weight=1, uniform="c")

        self._carte_stat(row1, "🎓", "Étudiants inscrits", str(nb_etudiants),
                         f"{nb_classes} classe(s)").grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        self._carte_stat(row1, "✅", "Taux de présence", f"{taux_presence_global}%",
                         "sur l'ensemble des séances",
                         couleur=COULEURS["succes"]).grid(row=0, column=1, padx=8, sticky="nsew")
        self._carte_stat(row1, "💰", "Recouvrement", f"{taux_recouv}%",
                         f"{nb_soldes} dossier(s) soldé(s)",
                         couleur="#d97706").grid(row=0, column=2, padx=8, sticky="nsew")
        self._carte_stat(row1, "📊", "Total perçu", f"{percu:,.0f} Ar".replace(",", " "),
                         f"sur {attendu:,.0f} Ar".replace(",", " "),
                         couleur=COULEURS["accent"]).grid(row=0, column=3, padx=(8, 0), sticky="nsew")

        row2 = ttk.Frame(self.zone, style="TFrame")
        row2.pack(fill='both', expand=True, pady=(0, 12))
        row2.columnconfigure((0, 1), weight=1, uniform="c")

        self._carte_liste(row2, "📚  Répartition par classe", repartition).grid(
            row=0, column=0, padx=(0, 8), pady=(0, 8), sticky="nsew")
        self._carte_liste(row2, "🏆  Top 3 assiduité", top_assidus).grid(
            row=0, column=1, padx=(8, 0), pady=(0, 8), sticky="nsew")
        self._carte_liste(row2, "📊  Moyenne par classe", moyennes).grid(
            row=1, column=0, padx=(0, 8), pady=(8, 0), sticky="nsew")

        compta_lignes = [
            ("Total attendu", f"{attendu:,.0f} Ar".replace(",", " ")),
            ("Total perçu", f"{percu:,.0f} Ar".replace(",", " ")),
            ("Reste à percevoir", f"{reste:,.0f} Ar".replace(",", " ")),
        ]
        self._carte_liste(row2, "💼  Détail comptabilité", compta_lignes).grid(
            row=1, column=1, padx=(8, 0), pady=(8, 0), sticky="nsew")


# ================== Génération PDF ==================
class PdfPage(PageAvecScroll):
    def __init__(self, parent, controleur):
        super().__init__(parent, "Génération PDF", "Liste des étudiants par classe")
        self.controleur = controleur
        self._construire_contenu()

    def _construire_contenu(self):
        carte = CarteOmbre(self.scrollable, padding=25)
        carte.pack(pady=20, padx=30, fill='x')
        c = carte.contenu()
        c.columnconfigure(0, weight=1)

        ttk.Label(c, text="Choisir une classe", style="CardMuted.TLabel").grid(row=0, column=0, sticky='w', pady=(0, 5))
        self.var_classe = tk.StringVar()
        self.combo_classe = ttk.Combobox(
            c,
            textvariable=self.var_classe,
            values=Eleve.obtenir_classes_existantes(),
            state="readonly",
            font=(POLICE, 11),
            postcommand=self._maj_classes
        )
        self.combo_classe.grid(row=1, column=0, sticky='ew', pady=(0, 15))
        self.combo_classe.bind("<<ComboboxSelected>>", self._afficher_apercu)

        self.btn_generer = ttk.Button(c, text="📄  Générer le PDF", style="Accent.TButton",
                                      command=self._generer_pdf, state='disabled')
        self.btn_generer.grid(row=2, column=0, sticky='w', pady=(10, 5))

        self.badge = Badge(c)
        self.badge.grid(row=3, column=0, pady=(15, 0), sticky="w")
        self.badge.grid_remove()

        ttk.Label(self.scrollable, text="Aperçu des étudiants", style="TLabel",
                  font=(POLICE, 12, 'bold')).pack(padx=30, anchor='w', pady=(15, 5))
        self.frame_apercu, self.tree_apercu = creer_treeview_etudiants(self.scrollable)
        self.frame_apercu.pack(padx=30, pady=(0, 25), fill='both', expand=True)

        self._maj_classes()

    def _maj_classes(self):
        self.combo_classe['values'] = Eleve.obtenir_classes_existantes()

    def _afficher_apercu(self, event=None):
        classe = self.var_classe.get().strip()
        if not classe:
            self.btn_generer.config(state='disabled')
            return
        for item in self.tree_apercu.get_children():
            self.tree_apercu.delete(item)
        etudiants = Eleve.obtenir_etudiants_par_classe(classe)
        for num, nom, prenom, cl in etudiants:
            ajouter_ligne(self.tree_apercu, (num, nom, prenom, cl))
        self.btn_generer.config(state='normal' if etudiants else 'disabled')
        if not etudiants:
            self.badge.maj("Aucun étudiant dans cette classe", "erreur")
            self.badge.grid()
        else:
            self.badge.grid_remove()

    def _generer_pdf(self):
        classe = self.var_classe.get().strip()
        if not classe:
            messagebox.showwarning("Classe", "Veuillez sélectionner une classe.")
            return

        etudiants = Eleve.obtenir_etudiants_par_classe(classe)
        if not etudiants:
            messagebox.showinfo("Aucun étudiant", "Aucun étudiant trouvé pour cette classe.")
            return

        chemin = filedialog.asksaveasfilename(
            title="Enregistrer le PDF",
            defaultextension=".pdf",
            initialfile=f"liste_{classe.replace(' ', '_')}.pdf",
            filetypes=[("Fichier PDF", "*.pdf")]
        )
        if not chemin:
            return

        try:
            GenerateurPDF.generer_liste_classe(classe, etudiants, chemin)
            self.badge.maj(f"✔ PDF généré : {os.path.basename(chemin)}", "succes")
            self.badge.grid()
        except Exception as e:
            self.badge.maj(f"✘ Erreur : {e}", "erreur")
            self.badge.grid()


# ================== Application principale ==================
class Application(tk.Tk):
    PAGES = [
        ("🏠", "Accueil", "accueil"),
        ("📊", "Tableau de bord", "dashboard"),
        ("📝", "Inscription", "inscription"),
        ("📊", "Ajout de notes", "notes"),
        ("🔍", "Recherche", "recherche"),
        ("ℹ️", "Infos étudiant", "infos"),
        ("💰", "Comptabilité", "comptabilite"),
        ("✅", "Présence", "presence"),
        ("📄", "Générer PDF", "pdf"),
    ]

    def __init__(self):
        super().__init__()
        self.title("Gestion Étudiants & Notes")
        self.geometry("1080x680")
        self.minsize(920, 600)
        self.configure(bg=COULEURS["bg"])

        self._configurer_styles()

        # La barre de statut est créée en premier pour garder sa place en bas
        self._creer_barre_statut()

        conteneur_principal = tk.Frame(self, bg=COULEURS["bg"])
        conteneur_principal.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(conteneur_principal, bg=COULEURS["sidebar"], width=235)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)
        self._creer_sidebar()

        self.conteneur = ttk.Frame(conteneur_principal, style="TFrame")
        self.conteneur.pack(side='left', fill='both', expand=True)

        self.pages = {
            "accueil": AccueilPage(self.conteneur, self),
            "dashboard": DashboardPage(self.conteneur, self),
            "inscription": InscriptionPage(self.conteneur, self),
            "notes": NotesPage(self.conteneur, self),
            "recherche": RecherchePage(self.conteneur, self),
            "infos": InfosPage(self.conteneur, self),
            "comptabilite": ComptabilitePage(self.conteneur, self),
            "presence": PresencePage(self.conteneur, self),
            "pdf": PdfPage(self.conteneur, self),
        }

        self.page_active = None
        self.page_active_key = None
        self.sidebar_visible = True
        self.afficher_page("accueil")

        # Raccourcis clavier : Ctrl+1..9 pour naviguer, Ctrl+B pour la sidebar
        for i, (_, _, key) in enumerate(self.PAGES, start=1):
            self.bind(f"<Control-Key-{i}>", lambda e, k=key: self.afficher_page(k))
        self.bind("<Control-b>", lambda e: self.toggle_sidebar())

        self._configurer_molette()

    # ---------- Styles ----------
    def _configurer_styles(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        C = COULEURS

        style.configure("TFrame", background=C["bg"])
        style.configure("Card.TFrame", background=C["blanc"], relief="flat", borderwidth=0)

        style.configure("TLabel", background=C["bg"], font=(POLICE, 10), foreground=C["texte"])
        style.configure("Card.TLabel", background=C["blanc"], font=(POLICE, 10), foreground=C["texte"])
        style.configure("CardMuted.TLabel", background=C["blanc"], font=(POLICE, 9),
                        foreground=C["texte_muet"])
        style.configure("Erreur.TLabel", background=C["blanc"], font=(POLICE, 8),
                        foreground=C["erreur"])
        style.configure("Header.TLabel", background=C["bg"], font=(POLICE, 20, 'bold'),
                        foreground=C["texte"])
        style.configure("SousHeader.TLabel", background=C["bg"], font=(POLICE, 10),
                        foreground=C["texte_muet"])

        # --- Boutons : plats, sans cadre de focus, avec survol ---
        style.configure("Accent.TButton", background=C["accent"], foreground="white",
                        font=(POLICE, 10, 'bold'), relief="flat", padding=(16, 9),
                        borderwidth=0, focusthickness=0, focuscolor=C["accent"],
                        bordercolor=C["accent"], lightcolor=C["accent"], darkcolor=C["accent"])
        style.map("Accent.TButton",
                  background=[("disabled", "#c7c9f5"), ("pressed", C["accent_hover"]),
                              ("active", C["accent_hover"])],
                  foreground=[("disabled", "white")],
                  bordercolor=[("active", C["accent_hover"]), ("pressed", C["accent_hover"])],
                  lightcolor=[("active", C["accent_hover"]), ("pressed", C["accent_hover"])],
                  darkcolor=[("active", C["accent_hover"]), ("pressed", C["accent_hover"])])

        style.configure("Secondary.TButton", background=C["blanc"], foreground=C["texte"],
                        font=(POLICE, 10), relief="flat", padding=(14, 8),
                        borderwidth=1, focusthickness=0, focuscolor=C["blanc"],
                        bordercolor=C["bordure_forte"], lightcolor=C["blanc"], darkcolor=C["blanc"])
        style.map("Secondary.TButton",
                  background=[("disabled", C["gris_clair"]), ("active", C["gris_clair"])],
                  foreground=[("disabled", C["texte_muet"])],
                  bordercolor=[("active", C["accent"])],
                  lightcolor=[("active", C["gris_clair"])],
                  darkcolor=[("active", C["gris_clair"])])

        # --- Champs de saisie : bordure fine, devient indigo au focus ---
        style.configure("TEntry", padding=8, relief="flat", fieldbackground="white",
                        foreground=C["texte"], font=(POLICE, 10), borderwidth=1,
                        bordercolor=C["bordure_forte"], lightcolor=C["bordure_forte"],
                        darkcolor=C["bordure_forte"], insertcolor=C["texte"])
        style.map("TEntry",
                  bordercolor=[("focus", C["accent"])],
                  lightcolor=[("focus", C["accent"])],
                  darkcolor=[("focus", C["accent"])],
                  fieldbackground=[("disabled", C["gris_clair"])])
        style.configure("Erreur.TEntry", padding=8, relief="flat", fieldbackground=C["erreur_bg"],
                        foreground=C["texte"], font=(POLICE, 10), borderwidth=1,
                        bordercolor=C["erreur"], lightcolor=C["erreur"], darkcolor=C["erreur"])
        style.map("Erreur.TEntry",
                  bordercolor=[("focus", C["erreur"])],
                  lightcolor=[("focus", C["erreur"])],
                  darkcolor=[("focus", C["erreur"])])

        # --- Combobox ---
        style.configure("TCombobox", padding=7, relief="flat", foreground=C["texte"],
                        fieldbackground="white", background=C["gris_clair"],
                        arrowcolor=C["texte_muet"], borderwidth=1,
                        bordercolor=C["bordure_forte"], lightcolor=C["bordure_forte"],
                        darkcolor=C["bordure_forte"])
        style.map("TCombobox",
                  fieldbackground=[("readonly", "white")],
                  selectbackground=[("readonly", "white")],
                  selectforeground=[("readonly", C["texte"])],
                  bordercolor=[("focus", C["accent"])],
                  lightcolor=[("focus", C["accent"])],
                  darkcolor=[("focus", C["accent"])],
                  arrowcolor=[("active", C["accent"])])
        self.option_add("*TCombobox*Listbox.font", (POLICE, 10))
        self.option_add("*TCombobox*Listbox.selectBackground", C["accent"])
        self.option_add("*TCombobox*Listbox.selectForeground", "white")
        self.option_add("*TCombobox*Listbox.borderWidth", 0)

        # --- Tableaux : sans cadre natif (on l'ajoute nous-mêmes), lignes aérées ---
        style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
        style.configure("Treeview", background="white", fieldbackground="white",
                        foreground=C["texte"], rowheight=30, font=(POLICE, 9), borderwidth=0)
        style.configure("Treeview.Heading", background=C["gris_clair"], foreground=C["texte"],
                        font=(POLICE, 9, 'bold'), relief="flat", padding=(8, 8), borderwidth=0)
        style.map("Treeview.Heading", background=[("active", C["bordure"])])

        def _map_sans_bug(option):
            # Contournement d'un bug de Tk 8.6.9 : les couleurs de tags masquent la sélection
            return [e for e in style.map("Treeview", query_opt=option)
                    if e[:2] != ("!disabled", "!selected")]

        style.map("Treeview",
                  background=_map_sans_bug("background") + [("selected", C["accent_light"])],
                  foreground=_map_sans_bug("foreground") + [("selected", C["texte"])])

        # --- Barre de défilement fine, sans flèches ---
        style.layout("Vertical.TScrollbar", [
            ("Vertical.Scrollbar.trough", {
                "sticky": "ns",
                "children": [("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]
            })
        ])
        style.configure("Vertical.TScrollbar", background=C["bordure_forte"],
                        troughcolor=C["bg"], bordercolor=C["bg"], lightcolor=C["bordure_forte"],
                        darkcolor=C["bordure_forte"], arrowsize=10, width=10, relief="flat",
                        gripcount=0)
        style.map("Vertical.TScrollbar", background=[("active", C["texte_muet"])],
                  lightcolor=[("active", C["texte_muet"])],
                  darkcolor=[("active", C["texte_muet"])])

    # ---------- Sidebar ----------
    def _creer_sidebar(self):
        marque = tk.Frame(self.sidebar, bg=COULEURS["sidebar"])
        marque.pack(fill='x', pady=(20, 10), padx=18)
        tk.Label(marque, text="🎓  ScolaGest", font=(POLICE, 14, "bold"),
                 bg=COULEURS["sidebar"], fg="white").pack(anchor="w")
        tk.Label(marque, text="Gestion scolaire", font=(POLICE, 8),
                 bg=COULEURS["sidebar"], fg="#8b93b0").pack(anchor="w")

        tk.Button(self.sidebar, text="☰  Réduire", font=(POLICE, 9),
                  bg=COULEURS["sidebar"], fg="#8b93b0", bd=0, relief="flat", anchor="w", padx=18,
                  activebackground=COULEURS["sidebar_active"], activeforeground="white",
                  cursor="hand2", command=self.toggle_sidebar).pack(fill='x', pady=(5, 15))

        self.boutons_sidebar = {}
        for icone, texte, page_key in self.PAGES:
            ligne = tk.Frame(self.sidebar, bg=COULEURS["sidebar"])
            ligne.pack(fill='x')
            indicateur = tk.Frame(ligne, bg=COULEURS["sidebar"], width=4)
            indicateur.pack(side="left", fill="y")
            btn = tk.Button(ligne, text=f"  {icone}   {texte}", font=(POLICE, 10, 'bold'),
                            bg=COULEURS["sidebar"], fg="#c3c9de", bd=0, relief="flat",
                            activebackground=COULEURS["sidebar_active"], activeforeground="white",
                            anchor="w", padx=14, pady=12, cursor="hand2",
                            command=lambda p=page_key: self.afficher_page(p))
            btn.pack(side="left", fill='x', expand=True)
            btn.bind("<Enter>", lambda e, b=btn, p=page_key: self._survol_sidebar(b, p, True))
            btn.bind("<Leave>", lambda e, b=btn, p=page_key: self._survol_sidebar(b, p, False))
            self.boutons_sidebar[page_key] = (btn, indicateur)

        pied = tk.Label(self.sidebar, text="v2.1 — design modernisé", font=(POLICE, 7),
                        bg=COULEURS["sidebar"], fg="#565d7a")
        pied.pack(side="bottom", pady=12)

    def _survol_sidebar(self, bouton, page_key, entree):
        if page_key == self.page_active_key:
            return
        bouton.config(bg=COULEURS["sidebar_active"] if entree else COULEURS["sidebar"])

    def _maj_sidebar_selection(self, page_key):
        for key, (btn, indicateur) in self.boutons_sidebar.items():
            if key == page_key:
                btn.config(bg=COULEURS["sidebar_selected"], fg="white")
                indicateur.config(bg=COULEURS["accent"])
            else:
                btn.config(bg=COULEURS["sidebar"], fg="#c3c9de")
                indicateur.config(bg=COULEURS["sidebar"])

    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar.pack_forget()
            self.sidebar_visible = False
            self.bouton_ouvrir = tk.Button(self.conteneur, text="☰", font=(POLICE, 14),
                                           bg=COULEURS["bg"], fg=COULEURS["texte"], bd=0,
                                           cursor="hand2", command=self.toggle_sidebar)
            self.bouton_ouvrir.place(x=8, y=8)
        else:
            self.sidebar.pack(side='left', fill='y', before=self.conteneur)
            self.sidebar_visible = True
            if hasattr(self, 'bouton_ouvrir'):
                self.bouton_ouvrir.destroy()
                del self.bouton_ouvrir

    # ---------- Barre de statut ----------
    def _creer_barre_statut(self):
        self.statut = tk.Frame(self, bg=COULEURS["gris_clair"], height=26)
        self.statut.pack(side="bottom", fill="x")
        tk.Frame(self, bg=COULEURS["bordure_forte"], height=1).pack(side="bottom", fill="x")
        self.label_statut = tk.Label(self.statut, text="", bg=COULEURS["gris_clair"],
                                     fg=COULEURS["texte_muet"], font=(POLICE, 8), anchor="w")
        self.label_statut.pack(side="left", padx=12)
        self.label_horloge = tk.Label(self.statut, bg=COULEURS["gris_clair"],
                                      fg=COULEURS["texte_muet"], font=(POLICE, 8))
        self.label_horloge.pack(side="right", padx=12)
        self._maj_horloge()

    def _maj_horloge(self):
        self.label_horloge.config(text=datetime.now().strftime("%d/%m/%Y  %H:%M:%S"))
        self.after(1000, self._maj_horloge)

    # ---------- Molette de défilement ----------
    def _configurer_molette(self):
        """Branche la molette (Windows / macOS / Linux) sur la page active."""
        self.bind_all("<MouseWheel>", self._sur_molette)   # Windows + macOS
        self.bind_all("<Button-4>", self._sur_molette)     # Linux : haut
        self.bind_all("<Button-5>", self._sur_molette)     # Linux : bas

        # Par défaut, une Combobox change de valeur avec la molette et bloque le
        # défilement de la page. On remplace ce comportement : la molette fait
        # défiler la page, comme partout ailleurs.
        def molette_combobox(event):
            self._sur_molette(event)
            return "break"
        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.bind_class("TCombobox", sequence, molette_combobox)

    @staticmethod
    def _pas_molette(event):
        """Nombre de 'crans' à défiler (négatif = vers le haut)."""
        if getattr(event, "num", None) == 4:
            return -1
        if getattr(event, "num", None) == 5:
            return 1
        delta = event.delta
        if delta == 0:
            return 0
        if sys.platform == "darwin":
            return -int(delta)
        pas = int(delta / 120) or (1 if delta > 0 else -1)
        return -pas

    def _sur_molette(self, event):
        """Fait défiler la page active quand on tourne la molette."""
        page = self.page_active
        canvas = getattr(page, "_canvas", None)
        if canvas is None:
            return

        pas = self._pas_molette(event)
        if pas == 0:
            return

        # Widget réellement sous le pointeur
        try:
            w = self.winfo_containing(event.x_root, event.y_root)
        except Exception:
            w = None

        # Si la souris est sur un tableau (ou zone de texte) qui a lui-même
        # assez de lignes pour défiler, on le laisse gérer sa propre molette.
        # S'il n'a rien à défiler, la page prend le relais (sinon la page
        # "reste bloquée" dès que la souris passe sur un tableau).
        if isinstance(w, (ttk.Treeview, tk.Text, tk.Listbox)):
            try:
                debut, fin = w.yview()
                if debut > 0.0 or fin < 1.0:
                    return
            except Exception:
                pass

        # Rien à défiler si tout le contenu est déjà visible
        debut, fin = canvas.yview()
        if debut <= 0.0 and fin >= 1.0:
            return
        canvas.yview_scroll(pas, "units")

    # ---------- Navigation ----------
    def afficher_page(self, page_key):
        if self.page_active:
            self.page_active.pack_forget()
        page = self.pages[page_key]
        page.pack(fill='both', expand=True)
        self.page_active = page
        self.page_active_key = page_key
        self._maj_sidebar_selection(page_key)
        titre = dict((k, t) for _, t, k in self.PAGES)[page_key]
        self.label_statut.config(
            text=f"Page active : {titre}   •   Ctrl+1 à 9 pour naviguer, Ctrl+B pour la barre latérale")

        # Remet la page en haut quand on y revient
        canvas = getattr(page, "_canvas", None)
        if canvas is not None:
            canvas.yview_moveto(0)

        # Recharge automatiquement le tableau de bord
        if page_key == "dashboard":
            try:
                page._charger()
            except Exception:
                pass


if __name__ == "__main__":
    app = Application()
    app.mainloop()