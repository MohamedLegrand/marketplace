from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.urls import reverse


def client_required(view):
    """Acces reserve aux acheteurs connectes. Redirige vers la connexion client
    (et non la connexion vendeur, qui est le LOGIN_URL global)."""

    @wraps(view)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(
                request.get_full_path(), reverse("catalogue:connexion")
            )
        if request.user.role != request.user.Role.ACHETEUR:
            raise PermissionDenied("Espace reserve aux acheteurs.")
        return view(request, *args, **kwargs)

    return _wrapped
