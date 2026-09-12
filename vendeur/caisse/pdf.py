"""Generation du rapport de caisse au format PDF (reportlab, pas de
dependance systeme, fonctionne tel quel sous Windows)."""
import io

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

BLEU = colors.HexColor("#2f6fed")
BLEU_FONCE = colors.HexColor("#132a4d")
GRIS_CLAIR = colors.HexColor("#f4f7fb")
BORDURE = colors.HexColor("#e4e9f2")


def generer_pdf(boutique, libelle_periode, donnees):
    tampon = io.BytesIO()
    doc = SimpleDocTemplate(
        tampon, pagesize=A4,
        topMargin=20 * mm, bottomMargin=18 * mm, leftMargin=18 * mm, rightMargin=18 * mm,
        title=f"Rapport de caisse - {boutique.nom}",
    )
    styles = getSampleStyleSheet()
    style_cellule = ParagraphStyle("cellule", parent=styles["Normal"], fontSize=8, leading=10)
    elements = []

    elements.append(Paragraph(f"Rapport de caisse — {boutique.nom}", styles["Title"]))
    elements.append(Paragraph(
        f"Periode : {libelle_periode} — genere le {timezone.now().strftime('%d/%m/%Y %H:%M')}",
        styles["Normal"],
    ))
    elements.append(Spacer(1, 8 * mm))

    kpi = [
        ["Chiffre d'affaires (commandes livrees)", f"{donnees['ca_livre']} XAF"],
        ["Commandes sur la periode", str(donnees["nb_commandes"])],
        ["Dont livrees", str(donnees["nb_commandes_livrees"])],
        ["Unites vendues", str(donnees["qte_vendue"])],
        ["Unites reapprovisionnees", str(donnees["qte_reappro"])],
    ]
    table_kpi = Table(kpi, colWidths=[100 * mm, 60 * mm])
    table_kpi.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GRIS_CLAIR),
        ("TEXTCOLOR", (0, 0), (-1, -1), BLEU_FONCE),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDURE),
    ]))
    elements.append(table_kpi)
    elements.append(Spacer(1, 10 * mm))

    elements.append(Paragraph("Mouvements de stock", styles["Heading2"]))
    entetes = ["Date", "Type", "Produit", "Qte", "Montant (XAF)"]
    lignes = [entetes]
    for m in donnees["mouvements"][:400]:
        nom_produit = str(m.produit) + (f" - {m.variante.libelle}" if m.variante else "")
        lignes.append([
            m.date_creation.strftime("%d/%m/%Y %H:%M"),
            m.get_type_mouvement_display(),
            Paragraph(nom_produit, style_cellule),
            str(m.quantite),
            str(m.montant) if m.montant else "—",
        ])
    if len(lignes) == 1:
        lignes.append(["—", "Aucun mouvement sur la periode", "", "", ""])

    table_mvt = Table(lignes, colWidths=[26 * mm, 30 * mm, 66 * mm, 14 * mm, 24 * mm], repeatRows=1)
    table_mvt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLEU),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDURE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLAIR]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(table_mvt)

    doc.build(elements)
    return tampon.getvalue()
