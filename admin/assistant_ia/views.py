import re

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, render

from vendeur.assistant.groq_client import GroqError, get_client

from .contexte import prompt_systeme
from .models import Conversation, MessageIA

# Nombre de messages recents renvoyes a l'IA a chaque question (fenetre de
# contexte limitee : on garde les echanges les plus recents).
MAX_HISTORIQUE = 12


def _nettoyer_markdown(texte):
    """Filet de securite : le prompt demande du texte brut, mais le modele
    laisse parfois echapper de la syntaxe Markdown (**gras**, ## titres).
    On la retire pour un affichage propre dans la bulle de discussion."""
    texte = re.sub(r"\*\*(.+?)\*\*", r"\1", texte)
    texte = re.sub(r"^#{1,6}\s*", "", texte, flags=re.MULTILINE)
    texte = re.sub(r"^-{3,}$", "", texte, flags=re.MULTILINE)
    return texte.strip()


@staff_member_required
def analyse(request):
    conversation, _cree = Conversation.objects.get_or_create(administrateur=request.user)

    if request.method == "POST" and request.POST.get("action") == "reinitialiser":
        conversation.messages.all().delete()
        messages.success(request, "Conversation reinitialisee.")
        return redirect("assistant_admin:analyse")

    if request.method == "POST":
        question = (request.POST.get("contenu") or "").strip()
        if question:
            MessageIA.objects.create(
                conversation=conversation, role=MessageIA.Role.UTILISATEUR, contenu=question
            )
            historique = list(conversation.messages.order_by("-date_creation")[:MAX_HISTORIQUE])
            historique.reverse()
            fil = [{"role": "system", "content": prompt_systeme(request.user)}]
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
        return redirect("assistant_admin:analyse")

    return render(request, "admin/assistant_ia/chat.html", {
        "historique": conversation.messages.all(),
    })
