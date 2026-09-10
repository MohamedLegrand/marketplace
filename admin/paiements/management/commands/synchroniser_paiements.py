from django.core.management.base import BaseCommand

from admin.paiements.services import synchroniser_paiements_en_attente


class Command(BaseCommand):
    help = (
        "Interroge l'agregateur (polling) pour tous les paiements encore en "
        "attente, applique les statuts SUCCESS / FAILED et confirme les "
        "commandes / abonnements associes. A programmer toutes les 1-2 minutes."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--timeout-min",
            type=int,
            default=None,
            help="Delai (minutes) au-dela duquel un paiement toujours PENDING est marque echoue.",
        )

    def handle(self, *args, **options):
        verifies, reussis, echoues = synchroniser_paiements_en_attente(
            timeout_min=options["timeout_min"]
        )
        self.stdout.write(self.style.SUCCESS(
            f"{verifies} paiement(s) verifie(s) : {reussis} reussi(s), {echoues} echoue(s)."
        ))
