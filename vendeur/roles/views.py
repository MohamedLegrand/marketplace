from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.crypto import get_random_string

from admin.abonnements.services import peut_creer_role
from admin.boutiques.models import Boutique, RoleBoutique
from vendeur.comptes.decorators import onboarding_complete_required

from .forms import AjoutMembreForm, RoleForm

User = get_user_model()


def _boutique(request, boutique_pk):
    return get_object_or_404(Boutique, pk=boutique_pk, proprietaire=request.user)


@onboarding_complete_required
def liste(request, boutique_pk):
    boutique = _boutique(request, boutique_pk)
    autorise, message = peut_creer_role(boutique)
    return render(request, "vendeur/roles/liste.html", {
        "boutique": boutique,
        "roles": boutique.roles.select_related("utilisateur"),
        "peut_ajouter": autorise,
        "message_quota": message,
    })


@onboarding_complete_required
def ajouter(request, boutique_pk):
    boutique = _boutique(request, boutique_pk)
    autorise, message = peut_creer_role(boutique)
    if not autorise:
        messages.error(request, message)
        return redirect("roles_vendeur:liste", boutique_pk=boutique_pk)

    form = AjoutMembreForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        if email == request.user.email:
            form.add_error("email", "Vous ne pouvez pas vous ajouter vous-meme.")
        else:
            membre = User.objects.filter(email=email).first()
            cree, mot_de_passe = False, None
            if membre is None:
                mot_de_passe = get_random_string(10)
                membre = User.objects.create_user(email=email, password=mot_de_passe)
                cree = True

            if RoleBoutique.objects.filter(boutique=boutique, utilisateur=membre).exists():
                if cree:
                    membre.delete()
                form.add_error("email", "Cette personne fait deja partie de l'equipe de cette boutique.")
            else:
                role = RoleBoutique(
                    boutique=boutique,
                    utilisateur=membre,
                    type_role=form.cleaned_data["type_role"],
                    libelle=form.cleaned_data["libelle"],
                    **form.permissions(),
                )
                try:
                    role.full_clean()
                    role.save()
                except ValidationError as err:
                    if cree:
                        membre.delete()
                    messages.error(request, " ".join(err.messages))
                    return redirect("roles_vendeur:liste", boutique_pk=boutique_pk)

                if cree:
                    messages.success(request, (
                        f"Membre ajoute. Mot de passe provisoire : {mot_de_passe} "
                        "- a lui transmettre (aucun e-mail n'est envoye)."
                    ))
                else:
                    messages.success(request, "Membre ajoute a l'equipe.")
                return redirect("roles_vendeur:liste", boutique_pk=boutique_pk)

    return render(request, "vendeur/roles/form.html", {
        "form": form, "boutique": boutique, "mode": "ajouter",
    })


@onboarding_complete_required
def modifier(request, boutique_pk, role_pk):
    boutique = _boutique(request, boutique_pk)
    role = get_object_or_404(RoleBoutique, pk=role_pk, boutique=boutique)
    form = RoleForm(request.POST or None, instance=role)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Role mis a jour.")
        return redirect("roles_vendeur:liste", boutique_pk=boutique_pk)
    return render(request, "vendeur/roles/form.html", {
        "form": form, "boutique": boutique, "role": role, "mode": "modifier",
    })


@onboarding_complete_required
def basculer_actif(request, boutique_pk, role_pk):
    boutique = _boutique(request, boutique_pk)
    role = get_object_or_404(RoleBoutique, pk=role_pk, boutique=boutique)
    if request.method == "POST":
        role.actif = not role.actif
        role.save(update_fields=["actif", "date_modification"])
        messages.success(request, "Membre " + ("active." if role.actif else "desactive."))
    return redirect("roles_vendeur:liste", boutique_pk=boutique_pk)


@onboarding_complete_required
def retirer(request, boutique_pk, role_pk):
    boutique = _boutique(request, boutique_pk)
    role = get_object_or_404(RoleBoutique, pk=role_pk, boutique=boutique)
    if request.method == "POST":
        role.delete()
        messages.success(request, "Membre retire de l'equipe (le compte n'est pas supprime).")
    return redirect("roles_vendeur:liste", boutique_pk=boutique_pk)
