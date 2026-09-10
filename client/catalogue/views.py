from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render, resolve_url
from django.utils.http import url_has_allowed_host_and_scheme

from admin.boutiques.models import Boutique
from admin.categories.models import Categorie
from admin.produits.models import Produit


def _destination_apres_connexion(user):
    """Espace vers lequel rediriger selon le role du compte."""
    role = getattr(user, "role", None)
    if user.is_staff or role == user.Role.ADMIN:
        return "/admin/"
    if role == user.Role.VENDEUR:
        return resolve_url("comptes_vendeur:tableau_de_bord")
    return resolve_url("comptes_client:tableau_de_bord")


def connexion(request):
    """Connexion unique (e-mail + mot de passe). Redirige automatiquement vers
    l'espace acheteur, vendeur ou l'administration selon le role du compte."""
    if request.user.is_authenticated:
        return redirect(_destination_apres_connexion(request.user))

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        auth_login(request, form.get_user())
        suivant = request.POST.get("next") or request.GET.get("next")
        if suivant and url_has_allowed_host_and_scheme(
            suivant, {request.get_host()}, request.is_secure()
        ):
            return redirect(suivant)
        return redirect(_destination_apres_connexion(form.get_user()))

    return render(request, "client/catalogue/connexion.html", {
        "form": form, "next": request.GET.get("next", ""),
    })


def inscription(request):
    return render(request, "client/catalogue/inscription.html")


def apropos(request):
    return render(request, "client/catalogue/apropos.html")


def landing(request):
    """Page d'accueil marketing de la marketplace."""
    boutiques = Boutique.objects.visibles().select_related("categorie")
    return render(request, "client/catalogue/landing.html", {
        "boutiques": boutiques[:6],
        "nb_boutiques": boutiques.count(),
        "etapes_achat": [
            ("i-search", "Parcourez", "Explorez les boutiques et les produits, filtrez par catégorie."),
            ("i-card", "Commandez", "Ajoutez au panier et payez par Mobile Money en toute sécurité."),
            ("i-truck", "Recevez", "La boutique prépare et livre votre commande dans votre zone."),
        ],
        "atouts_vendeur": [
            ("i-store", "Boutique en ligne"),
            ("i-package", "Catalogue & stock"),
            ("i-receipt", "Suivi des commandes"),
            ("i-user", "Rôles pour l'équipe"),
        ],
    })


def accueil(request):
    """Catalogue + recherche : boutiques, produits, filtre par categorie."""
    q = request.GET.get("q", "").strip()
    categorie_id = request.GET.get("categorie", "").strip()

    boutiques = Boutique.objects.visibles().select_related("categorie")
    produits = (
        Produit.objects.disponibles()
        .select_related("boutique", "categorie")
        .prefetch_related("photos")
        .filter(boutique__in=Boutique.objects.visibles())
    )

    if q:
        boutiques = boutiques.filter(
            Q(nom__icontains=q) | Q(ville__icontains=q) | Q(description__icontains=q)
        )
        produits = produits.filter(Q(nom__icontains=q) | Q(description__icontains=q))
    if categorie_id.isdigit():
        boutiques = boutiques.filter(categorie_id=categorie_id)
        produits = produits.filter(categorie_id=categorie_id)

    recherche_active = bool(q or categorie_id)
    if not recherche_active:
        produits = produits.none()

    return render(request, "client/catalogue/accueil.html", {
        "q": q,
        "categorie_id": categorie_id,
        "categories": Categorie.objects.filter(actif=True).order_by("type", "nom"),
        "boutiques": boutiques,
        "produits": produits[:60],
        "recherche_active": recherche_active,
    })


def boutique(request, boutique_slug):
    b = get_object_or_404(Boutique.objects.visibles(), slug=boutique_slug)
    produits = b.produits.disponibles().select_related("categorie").prefetch_related("photos")
    return render(request, "client/catalogue/boutique.html", {
        "boutique": b,
        "produits": produits,
        "zones": b.zones_livraison.filter(actif=True),
        "avis": b.avis.filter(statut="publie").select_related("auteur")[:20],
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
        "avis": p.avis.filter(statut="publie").select_related("auteur")[:30],
    })
