from django.http import HttpResponse
from django.shortcuts import render

from vendeur.comptes.decorators import acces_boutique_required

from .pdf import generer_pdf
from .services import LIBELLES_PERIODE, construire_rapport


def _periode(request):
    periode = request.GET.get("periode", "30j")
    return periode if periode in LIBELLES_PERIODE else "30j"


@acces_boutique_required("statistiques")
def rapport(request, boutique_pk):
    boutique = request.boutique
    periode = _periode(request)
    donnees = construire_rapport(boutique, periode)
    return render(request, "vendeur/caisse/rapport.html", {
        "boutique": boutique,
        "periode": periode,
        "periodes": LIBELLES_PERIODE.items(),
        "libelle_periode": LIBELLES_PERIODE[periode],
        **donnees,
        "mouvements_affiches": donnees["mouvements"][:50],
    })


@acces_boutique_required("statistiques")
def rapport_pdf(request, boutique_pk):
    boutique = request.boutique
    periode = _periode(request)
    donnees = construire_rapport(boutique, periode)
    contenu = generer_pdf(boutique, LIBELLES_PERIODE[periode], donnees)
    reponse = HttpResponse(contenu, content_type="application/pdf")
    nom_fichier = f"rapport-caisse-{boutique.slug}-{periode}.pdf"
    reponse["Content-Disposition"] = f'attachment; filename="{nom_fichier}"'
    return reponse
