from django.shortcuts import redirect, render

from client.comptes.decorators import client_required

from .models import Notification


@client_required
def liste(request):
    notifications = request.user.notifications.all()
    Notification.objects.filter(destinataire=request.user, lu=False).update(lu=True)
    return render(request, "client/notifications/liste.html", {
        "notifications": notifications,
    })


@client_required
def suivre(request, pk):
    """Marque la notification comme lue puis redirige vers son lien (ou la
    liste des notifications a defaut)."""
    notification = Notification.objects.filter(pk=pk, destinataire=request.user).first()
    if notification is None:
        return redirect("notifications_client:liste")
    if not notification.lu:
        notification.lu = True
        notification.save(update_fields=["lu"])
    return redirect(notification.lien or "notifications_client:liste")
