"""Categories de produit par defaut proposees a la creation d'un produit.

Le vendeur peut toujours choisir « Autres… » et preciser sa propre categorie
(elle est alors ajoutee automatiquement a la liste, voir
vendeur/produits/forms.py).
"""
from django.db import migrations
from django.utils.text import slugify

CATEGORIES_PRODUIT = [
    "Mode & Vêtements",
    "Chaussures & Accessoires",
    "Beauté & Cosmétiques",
    "Électronique & High-Tech",
    "Téléphones & Accessoires",
    "Informatique",
    "Maison & Décoration",
    "Électroménager",
    "Alimentation & Boissons",
    "Artisanat & Fait main",
    "Automobile & Moto",
    "Santé & Bien-être",
    "Enfants & Bébés",
    "Sports & Loisirs",
    "Livres & Fournitures",
]


def creer_categories(apps, schema_editor):
    Categorie = apps.get_model("categories", "Categorie")
    for ordre, nom in enumerate(CATEGORIES_PRODUIT, start=1):
        Categorie.objects.get_or_create(
            type="produit",
            nom=nom,
            defaults={
                "actif": True,
                "ordre": ordre,
                "slug": slugify(f"produit-{nom}"),
            },
        )


def supprimer_categories(apps, schema_editor):
    Categorie = apps.get_model("categories", "Categorie")
    Categorie.objects.filter(type="produit", nom__in=CATEGORIES_PRODUIT).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("categories", "0002_categories_boutique_initiales"),
    ]

    operations = [
        migrations.RunPython(creer_categories, supprimer_categories),
    ]
