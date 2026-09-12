from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from client.comptes.models import AdresseLivraison

from .decorators import client_required
from .forms import AdresseForm, InscriptionClientForm, ProfilClientForm

BACKEND = "django.contrib.auth.backends.ModelBackend"


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
        user = form.save()
        login(request, user, backend=BACKEND)
        messages.success(request, "Compte cree. Bienvenue !")
        return redirect("comptes_client:tableau_de_bord")
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
    next_page = reverse_lazy("catalogue:accueil")


class ChangerMotDePasse(PasswordChangeView):
    template_name = "client/comptes/mot_de_passe.html"
    success_url = reverse_lazy("comptes_client:tableau_de_bord")

    def form_valid(self, form):
        messages.success(self.request, "Mot de passe mis a jour.")
        return super().form_valid(form)


@client_required
def tableau_de_bord(request):
    return render(request, "client/comptes/tableau_de_bord.html", {
        "adresses": request.user.adresses.all(),
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
