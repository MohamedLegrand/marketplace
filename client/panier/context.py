from .panier import Panier


def panier(request):
    """Expose le nombre d'articles du panier a tous les templates."""
    try:
        nb = Panier(request).nb_articles()
    except Exception:
        nb = 0
    return {"panier_nb": nb}
