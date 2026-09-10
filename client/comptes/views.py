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
        return redirect("comptes_client:tableau_de_bord")
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
