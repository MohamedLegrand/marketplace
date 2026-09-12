from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
)
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from admin.abonnements.models import Abonnement, Plan
from admin.abonnements.services import abonnement_actif
from admin.kyc.models import DossierKYC
from admin.paiements.gateway import HRSkillsPayError
from admin.paiements.models import Paiement
from admin.paiements.services import (
    initier_paiement_abonnement,
    synchroniser_statut,
)

from .decorators import vendeur_required
from .forms import DossierKYCForm, InscriptionVendeurForm, ProfilVendeurForm
from . import onboarding

BACKEND = "django.contrib.auth.backends.ModelBackend"

_ETAPE_VERS_URL = {
    onboarding.PROFIL: "comptes_vendeur:profil",
    onboarding.IDENTITE: "comptes_vendeur:identite",
    onboarding.FORFAIT: "comptes_vendeur:forfait",
    onboarding.PAIEMENT: "comptes_vendeur:paiement",
}


def _rediriger_vers_etape(user):
    """Renvoie une redirection vers l'etape d'onboarding en cours, ou None."""
    etape = onboarding.etape_courante(user)
    cible = _ETAPE_VERS_URL.get(etape)
    return redirect(cible) if cible else None


# ---------------------------------------------------------------------------
# Authentification
# ---------------------------------------------------------------------------
def inscription(request):
    if request.user.is_authenticated:
        if request.user.role == request.user.Role.VENDEUR:
            return redirect("comptes_vendeur:tableau_de_bord")
        # Deja connecte, mais avec un autre type de compte (acheteur, admin...) :
        # rediriger vers le tableau de bord vendeur declencherait un 403
        # (page presque vide) au lieu du formulaire attendu. On affiche une
        # page claire et actionnable plutot qu'un simple message discret.
        return render(request, "vendeur/auth/deja_connecte.html", {
            "cible": "vendeur",
        })

    form = InscriptionVendeurForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend=BACKEND)
        messages.success(request, "Compte cree. Completons votre profil.")
        return redirect("comptes_vendeur:tableau_de_bord")
    return render(request, "vendeur/auth/inscription.html", {"form": form})


class Connexion(LoginView):
    template_name = "vendeur/auth/connexion.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        # `dispatch()` (utilisateur deja connecte) et `form_valid()` (connexion
        # qui vient de reussir) passent tous les deux par cette methode. Si le
        # role n'est pas vendeur, renvoyer vers le tableau de bord vendeur
        # declencherait un 403 (page presque vide) : on renvoie vers la page
        # d'inscription, qui affiche alors une explication claire.
        if self.request.user.role != self.request.user.Role.VENDEUR:
            return reverse_lazy("comptes_vendeur:inscription")
        return reverse_lazy("comptes_vendeur:tableau_de_bord")


class Deconnexion(LogoutView):
    next_page = reverse_lazy("catalogue:landing")


class ChangerMotDePasse(PasswordChangeView):
    template_name = "vendeur/auth/mot_de_passe.html"
    success_url = reverse_lazy("comptes_vendeur:tableau_de_bord")

    def form_valid(self, form):
        messages.success(self.request, "Mot de passe mis a jour.")
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Profil
# ---------------------------------------------------------------------------
@vendeur_required
def profil(request):
    form = ProfilVendeurForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profil enregistre.")
        return redirect("comptes_vendeur:tableau_de_bord")
    return render(
        request,
        "vendeur/auth/profil.html",
        {"form": form, "etape": onboarding.etape_courante(request.user)},
    )


# ---------------------------------------------------------------------------
# Onboarding - etape identite (KYC)
# ---------------------------------------------------------------------------
@vendeur_required
def onboarding_identite(request):
    user = request.user
    if not onboarding.profil_complet(user):
        return redirect("comptes_vendeur:profil")

    dossier = onboarding.dossier_kyc(user)
    if dossier and dossier.statut == DossierKYC.Statut.VALIDE:
        return redirect("comptes_vendeur:tableau_de_bord")

    if dossier and dossier.statut == DossierKYC.Statut.EN_ATTENTE:
        return render(request, "vendeur/onboarding/identite.html", {
            "dossier": dossier, "etape": onboarding.IDENTITE, "phase": "en_attente",
        })

    form = DossierKYCForm(
        request.POST or None, request.FILES or None, instance=dossier
    )
    if request.method == "POST" and form.is_valid():
        dossier = form.save(commit=False)
        dossier.vendeur = user
        dossier.soumettre()
        messages.success(request, "Dossier envoye. Il sera verifie par notre equipe.")
        return redirect("comptes_vendeur:tableau_de_bord")

    phase = "rejete" if (dossier and dossier.statut == DossierKYC.Statut.REJETE) else "formulaire"
    return render(request, "vendeur/onboarding/identite.html", {
        "form": form, "dossier": dossier, "etape": onboarding.IDENTITE, "phase": phase,
    })


# ---------------------------------------------------------------------------
# Onboarding - etape forfait
# ---------------------------------------------------------------------------
@vendeur_required
def onboarding_forfait(request):
    user = request.user
    etape = onboarding.etape_courante(user)
    # Accessible pour choisir (FORFAIT) ou changer un forfait pas encore paye (PAIEMENT).
    if etape not in (onboarding.FORFAIT, onboarding.PAIEMENT):
        redirection = _rediriger_vers_etape(user)
        return redirection or redirect("comptes_vendeur:tableau_de_bord")

    plans = Plan.objects.filter(actif=True)
    if request.method == "POST":
        plan = plans.filter(pk=request.POST.get("plan")).first()
        if not plan:
            messages.error(request, "Forfait invalide.")
        else:
            Abonnement.objects.filter(
                vendeur=user, statut=Abonnement.Statut.EN_ATTENTE
            ).delete()
            Abonnement.objects.create(vendeur=user, plan=plan, montant=plan.prix)
            messages.success(request, f"Forfait « {plan.nom} » selectionne. Finalisez le paiement.")
            return redirect("comptes_vendeur:paiement")
    return render(request, "vendeur/onboarding/forfait.html", {
        "plans": plans, "etape": onboarding.FORFAIT,
    })


# ---------------------------------------------------------------------------
# Onboarding - etape paiement (agregateur HR-Skills Pay)
# ---------------------------------------------------------------------------
@vendeur_required
def onboarding_paiement(request):
    user = request.user
    abonnement = (
        Abonnement.objects.filter(vendeur=user, statut=Abonnement.Statut.EN_ATTENTE)
        .select_related("plan")
        .first()
    )
    if abonnement is None:
        if abonnement_actif(user):
            return redirect("comptes_vendeur:tableau_de_bord")
        return redirect("comptes_vendeur:forfait")

    paiement = abonnement.paiements.order_by("-date_creation").first()

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "verifier" and paiement:
            try:
                synchroniser_statut(paiement)
            except HRSkillsPayError as err:
                messages.error(request, f"Verification impossible : {err.message or err.code}")
                return redirect("comptes_vendeur:paiement")
            if abonnement_actif(user):
                messages.success(request, "Paiement confirme. Votre boutique peut demarrer.")
                return redirect("comptes_vendeur:tableau_de_bord")
            paiement.refresh_from_db()
            if paiement.statut == Paiement.Statut.ECHOUE:
                messages.error(request, "Le paiement a echoue. Reessayez.")
        elif action == "initier":
            operateur = request.POST.get("operateur")
            telephone = (request.POST.get("telephone") or "").strip()
            if operateur not in dict(settings.OPERATEURS_MOBILE_MONEY) or not telephone:
                messages.error(request, "Choisissez un operateur et saisissez votre numero.")
            else:
                try:
                    initier_paiement_abonnement(abonnement, operateur, telephone)
                except HRSkillsPayError as err:
                    messages.error(request, f"Echec de l'initiation : {err.message or err.code}")
                else:
                    messages.success(
                        request,
                        "Paiement initie. Validez la demande sur votre telephone, puis cliquez sur Verifier.",
                    )
        return redirect("comptes_vendeur:paiement")

    return render(request, "vendeur/onboarding/paiement.html", {
        "abonnement": abonnement,
        "paiement": paiement,
        "operateurs": settings.OPERATEURS_MOBILE_MONEY,
        "etape": onboarding.PAIEMENT,
    })


# ---------------------------------------------------------------------------
# Tableau de bord
# ---------------------------------------------------------------------------
@vendeur_required
def tableau_de_bord(request):
    user = request.user
    if not onboarding.onboarding_termine(user):
        return _rediriger_vers_etape(user) or redirect("comptes_vendeur:profil")

    return render(request, "vendeur/tableau_de_bord.html", {
        "abonnement": abonnement_actif(user),
        "dossier": onboarding.dossier_kyc(user),
        "boutiques": user.boutiques.all(),
        "etape": onboarding.TERMINE,
    })
