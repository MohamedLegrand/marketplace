"""Ajoute `?v=<horodatage>` a l'URL d'un fichier statique.

Evite que le navigateur affiche une version en cache d'un CSS/JS apres
modification en developpement (le nom de fichier ne change jamais avec
`{% static %}` seul, donc Chrome peut servir l'ancienne copie indefiniment).
"""
import os

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static as static_url

register = template.Library()


@register.simple_tag
def static_v(path):
    url = static_url(path)
    fichier = finders.find(path)
    if fichier:
        try:
            return f"{url}?v={int(os.path.getmtime(fichier))}"
        except OSError:
            pass
    return url
