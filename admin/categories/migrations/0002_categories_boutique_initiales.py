"""Categories de boutique par defaut proposees a la creation d'une boutique.

Le vendeur peut toujours choisir « Autres… » et preciser sa propre categorie
(elle est alors ajoutee automatiquement a la liste, voir
vendeur/boutiques/forms.py).
"""
from django.db import migrations
from django.utils.text import slugify

CATEGORIES_BOUTIQUE = [
    "Mode & Vêtements",
    "Beauté & Cosmétiques",
    "Électronique & High-Tech",
    "Alimentation & Boissons",
    "Maison & Décoration",
    "Artisanat & Fait main",
    "Automobile & Moto",
    "Santé & Bien-être",
    "Enfants & Bébés",
    "Services",
]


def creer_categories(apps, schema_editor):
    Categorie = apps.get_model("categories", "Categorie")
    for ordre, nom in enumerate(CATEGORIES_BOUTIQUE, start=1):
        Categorie.objects.get_or_create(
            type="boutique",
            nom=nom,
            defaults={
                "actif": True,
                "ordre": ordre,
                "slug": slugify(f"boutique-{nom}"),
            },
        )


def supprimer_categories(apps, schema_editor):
    Categorie = apps.get_model("categories", "Categorie")
    Categorie.objects.filter(type="boutique", nom__in=CATEGORIES_BOUTIQUE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("categories", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(creer_categories, supprimer_categories),
    ]
