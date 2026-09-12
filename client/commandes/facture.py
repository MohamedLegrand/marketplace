"""Generation de la facture (recu de paiement) au format PDF, a partir des
donnees stockees (commande + transaction de paiement)."""
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

LIBELLES_OPERATEUR = {
    "orange": "Orange Money",
    "mtn": "MTN MoMo",
    "simulation": "Paiement simule",
}


def generer_facture(commande, paiement):
    tampon = io.BytesIO()
    doc = SimpleDocTemplate(
        tampon, pagesize=A4,
        topMargin=20 * mm, bottomMargin=18 * mm, leftMargin=18 * mm, rightMargin=18 * mm,
        title=f"Facture {commande.reference}",
    )
    styles = getSampleStyleSheet()
    style_cellule = ParagraphStyle("cellule", parent=styles["Normal"], fontSize=9, leading=11)
    elements = []

    elements.append(Paragraph("Jennifer Website", styles["Title"]))
    elements.append(Paragraph("Facture / reçu de paiement", styles["Heading2"]))
    elements.append(Spacer(1, 6 * mm))

    entete = [
        ["Commande", commande.reference],
        ["Date de la commande", commande.date_creation.strftime("%d/%m/%Y %H:%M")],
        ["Boutique", commande.boutique.nom],
        ["Client", commande.adresse_nom],
        ["Livraison", f"{commande.adresse_ville}" + (f", {commande.adresse_quartier}" if commande.adresse_quartier else "")],
    ]
    table_entete = Table(entete, colWidths=[45 * mm, 115 * mm])
    table_entete.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#5f7492")),
        ("TEXTCOLOR", (1, 0), (1, -1), BLEU_FONCE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(table_entete)
    elements.append(Spacer(1, 8 * mm))

    elements.append(Paragraph("Articles", styles["Heading3"]))
    # Le nom du produit (designation) est enveloppe dans un Paragraph pour
    # qu'un nom long passe a la ligne au lieu de deborder de la colonne ou
    # d'etre coupe : le nom exact du produit reste toujours entierement lisible.
    lignes = [["Désignation", "Qté", "Prix unitaire", "Sous-total"]]
    for l in commande.lignes.all():
        lignes.append([
            Paragraph(l.designation, style_cellule),
            str(l.quantite), f"{l.prix_unitaire} XAF", f"{l.sous_total} XAF",
        ])
    table_lignes = Table(lignes, colWidths=[80 * mm, 20 * mm, 30 * mm, 30 * mm], repeatRows=1)
    table_lignes.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLEU),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDURE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLAIR]),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(table_lignes)
    elements.append(Spacer(1, 4 * mm))

    totaux = [
        ["Sous-total", f"{commande.sous_total} XAF"],
        ["Livraison" + (f" ({commande.zone_nom})" if commande.zone_nom else ""), f"{commande.frais_livraison} XAF"],
        ["Total payé", f"{commande.total} XAF"],
    ]
    table_totaux = Table(totaux, colWidths=[130 * mm, 30 * mm])
    table_totaux.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("LINEABOVE", (0, 2), (-1, 2), 0.6, BLEU_FONCE),
        ("TOPPADDING", (0, 2), (-1, 2), 5),
    ]))
    elements.append(table_totaux)
    elements.append(Spacer(1, 10 * mm))

    elements.append(Paragraph("Paiement", styles["Heading3"]))
    paiement_info = [
        ["Statut", "Payé"],
        ["Moyen de paiement", LIBELLES_OPERATEUR.get(paiement.operateur, paiement.operateur or "—")],
        ["Référence de transaction", paiement.reference_externe],
        ["Date de confirmation", paiement.date_confirmation.strftime("%d/%m/%Y %H:%M") if paiement.date_confirmation else "—"],
        ["Montant", f"{paiement.montant} XAF"],
    ]
    table_paiement = Table(paiement_info, colWidths=[55 * mm, 105 * mm])
    table_paiement.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GRIS_CLAIR),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#5f7492")),
        ("TEXTCOLOR", (1, 0), (1, -1), BLEU_FONCE),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDURE),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(table_paiement)
    elements.append(Spacer(1, 10 * mm))

    elements.append(Paragraph(
        f"Document généré automatiquement le {timezone.now().strftime('%d/%m/%Y %H:%M')} — "
        "paiement simulé (aucun agrégateur externe).",
        styles["Normal"],
    ))

    doc.build(elements)
    return tampon.getvalue()
