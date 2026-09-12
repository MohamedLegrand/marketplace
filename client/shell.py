"""Choix du gabarit de page pour l'espace acheteur : un acheteur connecte
reste dans le shell du tableau de bord (barre laterale, sans header/footer
visiteur) meme en parcourant les boutiques, les produits, le panier et le
paiement ; les visiteurs (non connectes ou autre role) gardent le shell
public du site (header + footer)."""


def base_shell(request):
    user = request.user
    if user.is_authenticated and getattr(user, "role", None) == user.Role.ACHETEUR:
        return "client/dashboard_base.html"
    return "client/base.html"
