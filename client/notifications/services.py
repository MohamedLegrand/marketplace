from .models import Notification


def notifier(destinataire, titre, message, lien=""):
    """Cree une notification pour un utilisateur. Echoue silencieusement si
    ``destinataire`` est vide (ex. commande sans client, cas theorique)."""
    if destinataire is None:
        return None
    return Notification.objects.create(
        destinataire=destinataire, titre=titre, message=message, lien=lien,
    )
