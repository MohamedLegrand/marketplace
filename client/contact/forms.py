from django import forms

from client.contact.models import MessageContact


class ContactForm(forms.ModelForm):
    class Meta:
        model = MessageContact
        fields = ("nom", "email", "telephone", "message")
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}

    def clean(self):
        donnees = super().clean()
        if not donnees.get("email") and not donnees.get("telephone"):
            raise forms.ValidationError(
                "Indiquez au moins un e-mail ou un numero de telephone pour la reponse."
            )
        return donnees
