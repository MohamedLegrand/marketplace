from django import forms

from admin.avis.models import Avis


class AvisForm(forms.ModelForm):
    class Meta:
        model = Avis
        fields = ("note", "commentaire")
        widgets = {
            "note": forms.Select(choices=[(i, f"{i}/5") for i in range(1, 6)]),
            "commentaire": forms.Textarea(attrs={"rows": 4}),
        }
