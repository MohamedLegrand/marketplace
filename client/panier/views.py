from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from admin.boutiques.models import Boutique
from admin.produits.models import Produit

from .panier import Panier, PanierAutreBoutique


def voir(request):
    panier = Panier(request)
    boutique = None
    if panier.boutique_id:
        boutique = Boutique.objects.filter(pk=panier.boutique_id).first()
    return render(request, "client/panier/voir.html", {
        "lignes": panier.lignes(),
        "total": panier.total(),
        "boutique": boutique,
    })


def ajouter(request):
    if request.method != "POST":
        return redirect("catalogue:accueil")

    produit = get_object_or_404(Produit.objects.disponibles(), pk=request.POST.get("produit"))
    url_produit = redirect("catalogue:produit", boutique_slug=produit.boutique.slug, produit_slug=produit.slug)

    variante = None
    if produit.a_variantes:
        variante_id = request.POST.get("variante")
        variante = produit.variantes.filter(actif=True, pk=variante_id).first() if variante_id else None
        if variante is None:
            messages.error(request, "Choisissez une variante.")
            return url_produit

    stock = variante.stock if variante else produit.stock
    if stock <= 0:
        messages.error(request, "Ce produit est en rupture de stock.")
        return url_produit

    try:
        quantite = int(request.POST.get("quantite", 1))
    except (TypeError, ValueError):
        quantite = 1

    try:
        Panier(request).ajouter(produit, variante, quantite)
        messages.success(request, f"« {produit.nom} » ajoute au panier.")
    except PanierAutreBoutique:
        messages.error(
            request,
            "Votre panier contient deja des articles d'une autre boutique. "
            "Videz-le avant d'ajouter ce produit.",
        )
        return url_produit
    return redirect("panier:voir")


def modifier(request):
    if request.method == "POST":
        Panier(request).modifier(request.POST.get("cle", ""), request.POST.get("quantite", 0))
    return redirect("panier:voir")


def retirer(request):
    if request.method == "POST":
        Panier(request).retirer(request.POST.get("cle", ""))
        messages.success(request, "Article retire du panier.")
    return redirect("panier:voir")


def vider(request):
    if request.method == "POST":
        Panier(request).vider()
        messages.success(request, "Panier vide.")
    return redirect("panier:voir")
