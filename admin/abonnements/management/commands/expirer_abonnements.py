from django.core.management.base import BaseCommand
from django.utils import timezone

from admin.abonnements.models import Abonnement


class Command(BaseCommand):
    help = (
        "Passe au statut 'expire' les abonnements actifs dont l'echeance est "
        "depassee. A programmer (tache planifiee) pour le blocage automatique "
        "des boutiques en cas de non-renouvellement."
    )

    def handle(self, *args, **options):
        perimes = Abonnement.objects.filter(
            statut=Abonnement.Statut.ACTIF, date_fin__lt=timezone.now()
        )
        nombre = perimes.update(statut=Abonnement.Statut.EXPIRE)
        self.stdout.write(self.style.SUCCESS(f"{nombre} abonnement(s) expire(s)."))
