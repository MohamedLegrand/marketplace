"""Client de l'API Groq (chat completions, compatible OpenAI) pour
l'assistant IA d'analyse des ventes.

En l'absence de cle (GROQ_MOCK), une reponse simulee est renvoyee : aucun
appel reseau, utile en developpement hors-ligne ou pour previsualiser
l'interface sans consommer de credits API.
"""
from django.conf import settings


class GroqError(Exception):
    def __init__(self, message, details=None, http_status=None):
        self.message = message
        self.details = details or {}
        self.http_status = http_status
        super().__init__(message)


class GroqMock:
    """Simulation locale, sans reseau."""

    def repondre(self, messages, *, temperature=0.4, max_tokens=900):
        derniere = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
        )
        return (
            "(Mode demonstration - cle API Groq non configuree)\n\n"
            f"Question reçue : « {derniere[:200]} »\n\n"
            "Recommandations generales : mettez en avant vos produits les plus "
            "vendus sur la page d'accueil de la boutique, reapprovisionnez les "
            "articles en rupture de stock, et envisagez une remise temporaire "
            "sur les articles a faible rotation pour relancer la demande."
        )


class GroqClient:
    """Client HTTP reel (API compatible OpenAI)."""

    def __init__(self):
        import requests

        self._requests = requests
        self.base = "https://api.groq.com/openai/v1"
        self.key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL

    def repondre(self, messages, *, temperature=0.4, max_tokens=900):
        reponse = self._requests.post(
            f"{self.base}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=45,
        )
        try:
            data = reponse.json()
        except ValueError:
            data = {}
        if reponse.status_code >= 400:
            erreur = (data.get("error") or {}) if isinstance(data, dict) else {}
            message = erreur.get("message") or (reponse.text or "")[:200] or "Erreur API Groq."
            raise GroqError(message, data, reponse.status_code)
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError):
            raise GroqError("Reponse inattendue de l'API Groq.", data)


def get_client():
    if getattr(settings, "GROQ_MOCK", True) or not settings.GROQ_API_KEY:
        return GroqMock()
    return GroqClient()
