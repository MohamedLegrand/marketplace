from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from admin.boutiques.models import Boutique
from admin.categories.models import Categorie
from client.comptes.models import AdresseLivraison

from .decorators import client_required
from .forms import AdresseForm, InscriptionClientForm, ProfilClientForm


def inscription(request):
    if request.user.is_authenticated:
        if request.user.role == request.user.Role.ACHETEUR:
            return redirect("comptes_client:tableau_de_bord")
        # Deja connecte, mais avec un autre type de compte (vendeur, admin...) :
        # rediriger vers le tableau de bord acheteur declencherait un 403
        # (page presque vide) au lieu du formulaire attendu. On affiche une
        # page claire et actionnable plutot qu'un simple message discret.
        return render(request, "client/comptes/deja_connecte.html", {
            "cible": "acheteur",
        })
    form = InscriptionClientForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Compte créé avec succès. Connectez-vous pour continuer.")
        return redirect("catalogue:connexion")
    return render(request, "client/comptes/inscription.html", {"form": form})


class Connexion(LoginView):
    template_name = "client/comptes/connexion.html"
    redirect_authenticated_user = True
    next_page = reverse_lazy("comptes_client:tableau_de_bord")

    def get_default_redirect_url(self):
        # Utilisateur deja connecte avec un autre role : eviter le 403 en le
        # renvoyant vers la page d'inscription, qui affiche alors une
        # explication claire (au lieu d'un tableau de bord acheteur auquel
        # il n'a pas acces).
        if self.request.user.role != self.request.user.Role.ACHETEUR:
            return reverse_lazy("comptes_client:inscription")
        return super().get_default_redirect_url()


class Deconnexion(LogoutView):
    # Vers la landing page (presentation pure, sans panier) et non le
    # catalogue : coherent avec le comportement de la deconnexion vendeur.
    next_page = reverse_lazy("catalogue:landing")


class ChangerMotDePasse(PasswordChangeView):
    template_name = "client/comptes/mot_de_passe.html"
    success_url = reverse_lazy("comptes_client:tableau_de_bord")

    def form_valid(self, form):
        messages.success(self.request, "Mot de passe mis a jour.")
        return super().form_valid(form)


@client_required
def tableau_de_bord(request):
    from django.db.models import Sum

    from admin.commandes.models import Commande

    commandes = request.user.commandes.all()
    livrees = commandes.filter(statut=Commande.Statut.LIVREE)
    en_cours = commandes.exclude(
        statut__in=(Commande.Statut.LIVREE, Commande.Statut.ANNULEE)
    )
    return render(request, "client/comptes/tableau_de_bord.html", {
        "adresses": request.user.adresses.all(),
        "nb_commandes": commandes.count(),
        "nb_en_cours": en_cours.count(),
        "total_achete": livrees.aggregate(s=Sum("total"))["s"] or 0,
        "dernieres_commandes": commandes.select_related("boutique").prefetch_related("lignes")[:5],
    })


@client_required
def boutiques(request):
    """Liste des boutiques, accessible depuis le dashboard : on achete en
    cliquant sur une boutique (catalogue produits, panier, paiement simule)."""
    q = request.GET.get("q", "").strip()
    categorie_id = request.GET.get("categorie", "").strip()

    resultats = Boutique.objects.visibles().select_related("categorie")
    if q:
        resultats = resultats.filter(
            Q(nom__icontains=q) | Q(ville__icontains=q) | Q(description__icontains=q)
        )
    if categorie_id.isdigit():
        resultats = resultats.filter(categorie_id=categorie_id)

    return render(request, "client/comptes/boutiques.html", {
        "boutiques": resultats,
        "q": q,
        "categorie_id": categorie_id,
        "categories": Categorie.objects.filter(type=Categorie.Type.BOUTIQUE, actif=True).order_by("nom"),
    })


@client_required
def profil(request):
    form = ProfilClientForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profil enregistre.")
        return redirect("comptes_client:tableau_de_bord")
    return render(request, "client/comptes/profil.html", {"form": form})


# --- Adresses de livraison ------------------------------------------------
@client_required
def adresses(request):
    return render(request, "client/comptes/adresses.html", {
        "adresses": request.user.adresses.all(),
    })


@client_required
def adresse_creer(request):
    form = AdresseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        adresse = form.save(commit=False)
        adresse.client = request.user
        if not request.user.adresses.exists():
            adresse.par_defaut = True
        adresse.save()
        messages.success(request, "Adresse ajoutee.")
        return redirect("comptes_client:adresses")
    return render(request, "client/comptes/adresse_form.html", {"form": form, "mode": "creer"})


@client_required
def adresse_modifier(request, pk):
    adresse = get_object_or_404(AdresseLivraison, pk=pk, client=request.user)
    form = AdresseForm(request.POST or None, instance=adresse)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Adresse mise a jour.")
        return redirect("comptes_client:adresses")
    return render(request, "client/comptes/adresse_form.html", {
        "form": form, "mode": "modifier", "adresse": adresse,
    })


@client_required
def adresse_supprimer(request, pk):
    adresse = get_object_or_404(AdresseLivraison, pk=pk, client=request.user)
    if request.method == "POST":
        adresse.delete()
        messages.success(request, "Adresse supprimee.")
    return redirect("comptes_client:adresses")


@client_required
def adresse_defaut(request, pk):
    adresse = get_object_or_404(AdresseLivraison, pk=pk, client=request.user)
    if request.method == "POST":
        adresse.par_defaut = True
        adresse.save()
        messages.success(request, "Adresse par defaut definie.")
    return redirect("comptes_client:adresses")
