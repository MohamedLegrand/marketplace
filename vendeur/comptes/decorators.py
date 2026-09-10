from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def vendeur_required(view):
    """Acces reserve aux utilisateurs connectes ayant le role vendeur."""

    @wraps(view)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if request.user.role != request.user.Role.VENDEUR:
            raise PermissionDenied("Espace reserve aux vendeurs.")
        return view(request, *args, **kwargs)

    return _wrapped


def onboarding_complete_required(view):
    """Acces reserve aux vendeurs dont l'onboarding (profil + KYC + abonnement)
    est termine. Sinon, renvoi vers le tableau de bord qui aiguille vers
    l'etape en cours."""

    @wraps(view)
    @vendeur_required
    def _wrapped(request, *args, **kwargs):
        from .onboarding import onboarding_termine

        if not onboarding_termine(request.user):
            return redirect("comptes_vendeur:tableau_de_bord")
        return view(request, *args, **kwargs)

    return _wrapped
