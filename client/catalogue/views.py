from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from admin.boutiques.models import Boutique


def accueil(request):
    boutiques = Boutique.objects.visibles().select_related("categorie")
    recherche = request.GET.get("q", "").strip()
    if recherche:
        boutiques = boutiques.filter(
            Q(nom__icontains=recherche) | Q(ville__icontains=recherche)
        )
    return render(request, "client/catalogue/accueil.html", {
        "boutiques": boutiques,
        "recherche": recherche,
    })


def boutique(request, boutique_slug):
    b = get_object_or_404(Boutique.objects.visibles(), slug=boutique_slug)
    produits = b.produits.disponibles().select_related("categorie").prefetch_related("photos")
    return render(request, "client/catalogue/boutique.html", {
        "boutique": b,
        "produits": produits,
        "zones": b.zones_livraison.filter(actif=True),
    })


def produit(request, boutique_slug, produit_slug):
    b = get_object_or_404(Boutique.objects.visibles(), slug=boutique_slug)
    p = get_object_or_404(
        b.produits.disponibles().prefetch_related("photos", "variantes"),
        slug=produit_slug,
    )
    return render(request, "client/catalogue/produit.html", {
        "boutique": b,
        "produit": p,
        "photos": p.photos.all(),
        "variantes": p.variantes.filter(actif=True),
    })
