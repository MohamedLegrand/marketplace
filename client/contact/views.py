from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import ContactForm

WHATSAPP_NUMERO = "237650808714"
WHATSAPP_AFFICHE = "+237 6 50 80 87 14"
EMAIL_CONTACT = "contact@marketplace.cm"


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Message envoye. Nous vous repondrons rapidement.")
        return redirect("contact:contact")
    return render(request, "client/contact/contact.html", {
        "form": form,
        "whatsapp_numero": WHATSAPP_NUMERO,
        "whatsapp_affiche": WHATSAPP_AFFICHE,
        "email_contact": EMAIL_CONTACT,
    })
