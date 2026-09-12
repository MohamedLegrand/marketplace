import re

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from admin.abonnements.services import peut_utiliser_ia
from admin.boutiques.models import Boutique
from vendeur.comptes.decorators import onboarding_complete_required

from .contexte import prompt_systeme
from .groq_client import GroqError, get_client
from .models import Conversation, MessageIA

# Nombre de messages recents renvoyes a l'IA a chaque question (fenetre de
# contexte limitee : on garde les echanges les plus recents).
MAX_HISTORIQUE = 12


def _boutique(request, boutique_pk):
    return get_object_or_404(Boutique, pk=boutique_pk, proprietaire=request.user)


def _nettoyer_markdown(texte):
    """Filet de securite : le prompt demande du texte brut, mais le modele
    laisse parfois echapper de la syntaxe Markdown (**gras**, ## titres).
    On la retire pour un affichage propre dans la bulle de discussion."""
    texte = re.sub(r"\*\*(.+?)\*\*", r"\1", texte)
    texte = re.sub(r"^#{1,6}\s*", "", texte, flags=re.MULTILINE)
    texte = re.sub(r"^-{3,}$", "", texte, flags=re.MULTILINE)
    return texte.strip()


@onboarding_complete_required
def chat(request, boutique_pk):
    boutique = _boutique(request, boutique_pk)
    autorise, motif = peut_utiliser_ia(request.user)
    if not autorise:
        from admin.abonnements.models import Plan

        return render(request, "vendeur/assistant/verrouille.html", {
            "boutique": boutique,
            "motif": motif,
            "plans": Plan.objects.filter(actif=True, ia_analyse_ventes=True),
        })

    conversation, _cree = Conversation.objects.get_or_create(boutique=boutique)

    if request.method == "POST" and request.POST.get("action") == "reinitialiser":
        conversation.messages.all().delete()
        messages.success(request, "Conversation reinitialisee.")
        return redirect("assistant_vendeur:chat", boutique_pk=boutique.pk)

    if request.method == "POST":
        question = (request.POST.get("contenu") or "").strip()
        if question:
            MessageIA.objects.create(
                conversation=conversation, role=MessageIA.Role.UTILISATEUR, contenu=question
            )
            historique = list(conversation.messages.order_by("-date_creation")[:MAX_HISTORIQUE])
            historique.reverse()
            fil = [{"role": "system", "content": prompt_systeme(boutique)}]
            fil += [
                {
                    "role": "user" if m.role == MessageIA.Role.UTILISATEUR else "assistant",
                    "content": m.contenu,
                }
                for m in historique
            ]
            try:
                reponse = _nettoyer_markdown(get_client().repondre(fil))
            except GroqError as err:
                reponse = (
                    "Desole, une erreur est survenue lors de la generation de la "
                    f"reponse ({err.message}). Reessayez dans un instant."
                )
            MessageIA.objects.create(
                conversation=conversation, role=MessageIA.Role.ASSISTANT, contenu=reponse
            )
        return redirect("assistant_vendeur:chat", boutique_pk=boutique.pk)

    return render(request, "vendeur/assistant/chat.html", {
        "boutique": boutique,
        "historique": conversation.messages.all(),
    })
