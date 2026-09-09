from django.db import migrations

PLANS = [
    {
        "slug": "essentiel",
        "nom": "Essentiel",
        "prix": 5000,
        "ordre": 1,
        "max_boutiques": 1,
        "max_roles": 3,
        "delegation_roles": True,
        "ia_analyse_ventes": False,
        "description": "1 boutique. Delegation de roles limitee (jusqu'a 3).",
    },
    {
        "slug": "pro",
        "nom": "Pro",
        "prix": 10000,
        "ordre": 2,
        "max_boutiques": None,
        "max_roles": None,
        "delegation_roles": True,
        "ia_analyse_ventes": False,
        "description": "Boutiques et roles delegues illimites.",
    },
    {
        "slug": "premium",
        "nom": "Premium",
        "prix": 20000,
        "ordre": 3,
        "max_boutiques": None,
        "max_roles": None,
        "delegation_roles": True,
        "ia_analyse_ventes": True,
        "description": "Boutiques et roles illimites + IA d'analyse des ventes.",
    },
]


def creer_plans(apps, schema_editor):
    Plan = apps.get_model("abonnements", "Plan")
    for data in PLANS:
        # get_or_create : ne surcharge pas les prix ajustes ensuite par l'admin.
        Plan.objects.get_or_create(slug=data["slug"], defaults=data)


def supprimer_plans(apps, schema_editor):
    Plan = apps.get_model("abonnements", "Plan")
    Plan.objects.filter(slug__in=[p["slug"] for p in PLANS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("abonnements", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(creer_plans, supprimer_plans),
    ]
