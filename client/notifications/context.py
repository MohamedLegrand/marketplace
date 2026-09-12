def notifications(request):
    """Expose le nombre de notifications non lues a tous les templates
    (utilise par la barre laterale du dashboard acheteur)."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {"notifications_non_lues": 0}
    try:
        nb = user.notifications.filter(lu=False).count()
    except Exception:
        nb = 0
    return {"notifications_non_lues": nb}
