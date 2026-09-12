"""Jeu de donnees de demonstration pour le tableau de bord de l'admin.

    python manage.py demo_data          # cree / rafraichit les donnees demo
    python manage.py demo_data --clear  # supprime uniquement les donnees demo

Toutes les lignes creees sont prefixees / suffixees ("@demo.cm", "DMO-",
"demo-b-", idempotency_key "demo-dash-...") pour pouvoir etre retirees sans
toucher aux vraies donnees.
"""
from __future__ import annotations

import datetime
import random

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import transaction

TAG = "demo-dash"

CMD_STATUTS = [
    "confirmee", "en_preparation", "expediee",
    "livree", "livree", "livree", "annulee", "en_attente_paiement",
]
OPERATEURS = ["orange", "orange", "orange", "mtn", "mtn", "camtel"]
PAY_STATUTS = ["reussi"] * 12 + ["en_attente"] * 3 + ["echoue"] * 3 + ["rembourse"] * 1
VILLES = ["Douala", "Yaoundé", "Bafoussam", "Kribi", "Garoua"]


class Command(BaseCommand):
    help = "Cree ou supprime le jeu de donnees de demonstration du tableau de bord."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear", action="store_true",
            help="Supprime les donnees de demonstration puis s'arrete.",
        )
        parser.add_argument(
            "--jours", type=int, default=14,
            help="Nombre de jours d'historique a generer (defaut : 14).",
        )

    def handle(self, *args, **options):
        User = apps.get_model("account", "User")
        Boutique = apps.get_model("boutiques", "Boutique")
        Commande = apps.get_model("commandes", "Commande")
        Paiement = apps.get_model("paiements", "Paiement")
        DossierKYC = apps.get_model("kyc", "DossierKYC")

        with transaction.atomic():
            n = (
                Paiement.objects.filter(idempotency_key__startswith=TAG).delete()[0]
                + Commande.objects.filter(reference__startswith="DMO-").delete()[0]
                + Boutique.objects.filter(slug__startswith="demo-b-").delete()[0]
                + User.objects.filter(email__endswith="@demo.cm").delete()[0]
            )
            self.stdout.write(f"Donnees demo existantes supprimees ({n} objets).")
            if options["clear"]:
                self.stdout.write(self.style.SUCCESS("Terminé."))
                return

            random.seed(42)
            jours = max(3, options["jours"])

            vendeurs = []
            for i in range(3):
                u = User(
                    email=f"vendeur{i}@demo.cm", username=f"vendeur{i}_demo", role="vendeur",
                    first_name=random.choice(["Paul", "Aïcha", "Jean", "Ngo", "Samuel"]),
                    last_name=random.choice(["Kamdem", "Fotso", "Mballa", "Awono", "Nkeng"]),
                    telephone=f"69{random.randint(1_000_000, 9_999_999)}", is_active=True,
                )
                u.set_password("demo12345")
                u.save()
                vendeurs.append(u)

            boutiques = []
            for i in range(5):
                b = Boutique(
                    proprietaire=random.choice(vendeurs), nom=f"Boutique Démo {i + 1}",
                    slug=f"demo-b-{i + 1}", description="Boutique de démonstration.",
                    telephone=f"69{random.randint(1_000_000, 9_999_999)}", email=f"b{i}@demo.cm",
                    adresse="Rue du Marché", ville=random.choice(VILLES),
                    statut="approuvee" if i < 4 else "en_attente",
                )
                b.save()
                boutiques.append(b)

            acheteurs = []
            for i in range(4):
                u = User(
                    email=f"client{i}@demo.cm", username=f"client{i}_demo", role="acheteur",
                    first_name="Client", last_name=f"N{i}",
                    telephone=f"67{random.randint(1_000_000, 9_999_999)}", is_active=True,
                )
                u.set_password("demo12345")
                u.save()
                acheteurs.append(u)

            for v in vendeurs[:2]:
                if not DossierKYC.objects.filter(vendeur=v).exists():
                    DossierKYC.objects.create(
                        vendeur=v, nom_complet=v.get_full_name() or v.email,
                        type_piece="cni", numero_piece=str(random.randint(10 ** 9, 10 ** 10)),
                        statut="en_attente",
                    )

            actives = [b for b in boutiques if b.statut == "approuvee"]
            today = datetime.date.today()
            n_cmd = n_pay = 0
            for d in range(jours):
                jour = today - datetime.timedelta(days=jours - 1 - d)
                base = 3 + int(6 * (1 - abs(d - jours / 2) / (jours / 2)))
                for _ in range(random.randint(base, base + 4)):
                    b = random.choice(actives)
                    cli = random.choice(acheteurs)
                    sous_total = random.choice([2, 3, 5, 8, 12, 20, 35]) * 1000
                    frais_liv = random.choice([500, 1000, 1500, 2000])
                    total = sous_total + frais_liv
                    dt = datetime.datetime.combine(
                        jour, datetime.time(random.randint(7, 21), random.randint(0, 59))
                    )
                    c = Commande(
                        reference=f"DMO-{jour:%y%m%d}-{n_cmd:03d}", client=cli, boutique=b,
                        adresse_nom=cli.get_full_name() or "Client",
                        adresse_telephone=cli.telephone, adresse_ville=b.ville,
                        adresse_quartier="Centre", adresse_details="—", zone_nom="Centre-ville",
                        frais_livraison=frais_liv, sous_total=sous_total, total=total,
                        statut=random.choice(CMD_STATUTS),
                    )
                    c.save()
                    Commande.objects.filter(pk=c.pk).update(date_creation=dt)
                    n_cmd += 1

                    st = random.choice(PAY_STATUTS)
                    frais = int(total * 0.018)
                    p = Paiement(
                        type="commande", commande=c, montant=total, frais=frais,
                        montant_net=total - frais, devise="XAF",
                        operateur=random.choice(OPERATEURS), telephone=cli.telephone, statut=st,
                        idempotency_key=f"{TAG}-{n_pay:04d}",
                        reference_externe=f"REF{random.randint(10 ** 7, 10 ** 8)}",
                    )
                    p.save()
                    Paiement.objects.filter(pk=p.pk).update(
                        date_creation=dt,
                        date_confirmation=dt + datetime.timedelta(minutes=3) if st == "reussi" else None,
                    )
                    n_pay += 1

        self.stdout.write(self.style.SUCCESS(
            f"OK : {len(vendeurs)} vendeurs, {len(boutiques)} boutiques, "
            f"{len(acheteurs)} acheteurs, {n_cmd} commandes, {n_pay} paiements."
        ))
