from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from datetime import datetime
import os


class GenerateurPDF:
    @staticmethod
    def generer_liste_classe(classe, etudiants, chemin_sortie):
        """
        Génère un PDF listant les étudiants de la classe.
        
        :param classe: nom de la classe (ex: "L1")
        :param etudiants: liste de tuples (numero, nom, prenom, classe)
        :param chemin_sortie: chemin complet du fichier PDF à créer
        """
        if not etudiants:
            raise ValueError("Aucun étudiant trouvé pour cette classe.")

        # Créer le dossier parent si nécessaire
        dossier = os.path.dirname(chemin_sortie)
        if dossier and not os.path.exists(dossier):
            os.makedirs(dossier)

        doc = SimpleDocTemplate(
            chemin_sortie,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )

        styles = getSampleStyleSheet()
        style_titre = ParagraphStyle(
            'Titre',
            parent=styles['Title'],
            fontSize=18,
            textColor=colors.HexColor('#1e2430'),
            spaceAfter=6
        )
        style_sous_titre = ParagraphStyle(
            'SousTitre',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#6b7280'),
            spaceAfter=20
        )
        style_normal = styles['Normal']

        elements = []

        # Titre
        elements.append(Paragraph(f"Liste des étudiants – Classe {classe}", style_titre))
        elements.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}", style_sous_titre))
        elements.append(Spacer(1, 20))

        # Préparer les données du tableau
        data = [["N°", "Nom", "Prénom", "Classe"]]
        for numero, nom, prenom, classe_etudiant in etudiants:
            data.append([str(numero), nom, prenom, classe_etudiant])

        # Créer le tableau
        table = Table(data, colWidths=[50, 180, 180, 80])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#151a2d')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#1e2430')),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (1, 1), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])
        ]))

        elements.append(table)
        doc.build(elements)