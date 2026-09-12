from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect


def vendeur_required(view):
    """Acces reserve aux proprietaires de boutique (role vendeur). N'accepte
    pas les membres d'equipe (caissier, vendeur delegue...) : reserve aux
    ecrans de gestion du compte proprietaire lui-meme (onboarding, KYC,
    abonnement, creation de boutique, gestion de l'equipe)."""

    @wraps(view)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if request.user.role != request.user.Role.VENDEUR:
            raise PermissionDenied("Espace reserve aux vendeurs.")
        return view(request, *args, **kwargs)

    return _wrapped


def onboarding_complete_required(view):
    """Acces reserve aux vendeurs (proprietaires) dont l'onboarding
    (profil + KYC + abonnement) est termine. Sinon, renvoi vers le tableau de
    bord qui aiguille vers l'etape en cours."""

    @wraps(view)
    @vendeur_required
    def _wrapped(request, *args, **kwargs):
        from .onboarding import onboarding_termine

        if not onboarding_termine(request.user):
            return redirect("comptes_vendeur:tableau_de_bord")
        return view(request, *args, **kwargs)

    return _wrapped


def espace_vendeur_required(view):
    """Acces reserve a quiconque a un pied dans l'espace vendeur : le
    proprietaire (role vendeur) ou un membre d'equipe auquel un role a ete
    delegue sur au moins une boutique."""

    @wraps(view)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not request.user.peut_acceder_espace_vendeur:
            raise PermissionDenied("Espace reserve aux vendeurs et a leur equipe.")
        return view(request, *args, **kwargs)

    return _wrapped


def acces_boutique_required(permission=None):
    """Acces a une boutique precise (``boutique_pk`` dans l'URL), ouvert au
    proprietaire ET a tout membre d'equipe ayant un role actif sur cette
    boutique. ``permission`` restreint en plus l'acces au proprietaire ou a
    un membre disposant du champ booleen correspondant sur son
    ``RoleBoutique`` (``"produits"``, ``"stock"``, ``"commandes"`` ou
    ``"statistiques"``) ; laisser a ``None`` pour une simple consultation,
    ouverte a tout membre actif quel que soit son role.

    La vue recoit en plus, sur ``request`` :
    - ``request.boutique`` : la boutique resolue ;
    - ``request.est_proprietaire_boutique`` : True si l'utilisateur est le
      proprietaire ;
    - ``request.role_boutique`` : son ``RoleBoutique`` (ou None si
      proprietaire).
    """
    champ_permission = {
        "produits": "peut_gerer_produits",
        "stock": "peut_gerer_stock",
        "commandes": "peut_gerer_commandes",
        "statistiques": "peut_voir_statistiques",
    }.get(permission)

    def decorateur(view):
        @wraps(view)
        @login_required
        def _wrapped(request, boutique_pk, *args, **kwargs):
            from admin.boutiques.models import Boutique, RoleBoutique

            boutique = get_object_or_404(Boutique, pk=boutique_pk)

            if boutique.proprietaire_id == request.user.id:
                from .onboarding import onboarding_termine

                if not onboarding_termine(request.user):
                    return redirect("comptes_vendeur:tableau_de_bord")
                request.boutique = boutique
                request.est_proprietaire_boutique = True
                request.role_boutique = None
                return view(request, boutique_pk, *args, **kwargs)

            role = RoleBoutique.objects.filter(
                boutique=boutique, utilisateur=request.user, actif=True
            ).first()
            if role is None:
                raise PermissionDenied("Vous n'avez pas acces a cette boutique.")
            if champ_permission and not getattr(role, champ_permission, False):
                raise PermissionDenied(
                    "Votre role dans cette boutique ne vous donne pas cette permission."
                )
            request.boutique = boutique
            request.est_proprietaire_boutique = False
            request.role_boutique = role
            return view(request, boutique_pk, *args, **kwargs)

        return _wrapped

    return decorateur
