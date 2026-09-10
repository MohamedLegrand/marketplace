"""Client de l'agregateur de paiement HR-Skills Pay (Cash-In Mobile Money).

Doc : api.hrskills-pay.com — double cle (A dans Authorization: Bearer, B echangee
une fois contre un transaction token JWT valable 45 min) + Idempotency-Key sur
les POST.

En l'absence de cles (HRSKILLS_MOCK), un client simule est utilise : il suit le
contrat sandbox « montant pair -> SUCCESS, impair -> FAILED ».
"""
import time
import uuid

from django.conf import settings


class HRSkillsPayError(Exception):
    def __init__(self, code, message="", details=None, http_status=None):
        self.code = code
        self.message = message
        self.details = details or {}
        self.http_status = http_status
        super().__init__(f"{code}: {message}")


class GatewayMock:
    """Simulation locale, sans reseau."""

    def cash_in(self, *, operator, phone_number, amount, currency="XAF", country="CM",
                description="", metadata=None, idempotency_key=None):
        marqueur = "S" if int(amount) % 2 == 0 else "F"
        reference = f"ref_mock{marqueur}_{uuid.uuid4().hex[:12]}"
        frais = round(int(amount) * 0.015)
        return {"success": True, "data": {
            "transaction_id": str(uuid.uuid4()),
            "reference": reference,
            "status": "PENDING",
            "type": "CASHIN",
            "amount": int(amount),
            "fee": frais,
            "net_amount": int(amount) - frais,
            "currency": currency,
            "operator": operator,
            "phone_number": phone_number,
        }}

    def statut_paiement(self, reference):
        statut = "SUCCESS" if "_mockS_" in reference else "FAILED"
        return {"success": True, "data": {"reference": reference, "status": statut}}


class GatewayHRSkills:
    """Client HTTP reel."""

    def __init__(self):
        import requests

        self._requests = requests
        self.base = settings.HRSKILLS_BASE_URL.rstrip("/")
        self.key_a = settings.HRSKILLS_KEY_A
        self.key_b = settings.HRSKILLS_KEY_B
        self._token = None
        self._expire_a = 0.0

    def _token_valide(self):
        if self._token and time.time() < self._expire_a - 60:
            return self._token
        reponse = self._requests.post(
            f"{self.base}/v1/auth/transaction-token",
            headers={"Authorization": f"Bearer {self.key_a}", "Content-Type": "application/json"},
            json={"api_secret": self.key_b},
            timeout=20,
        )
        data = self._json_ou_erreur(reponse)
        self._token = data["transaction_token"]
        self._expire_a = time.time() + int(data.get("expires_in", 2700))
        return self._token

    def _headers(self, idempotency_key=None):
        entetes = {
            "Authorization": f"Bearer {self.key_a}",
            "X-Transaction-Token": self._token_valide(),
            "Content-Type": "application/json",
        }
        if idempotency_key:
            entetes["Idempotency-Key"] = idempotency_key
        return entetes

    def cash_in(self, *, operator, phone_number, amount, currency="XAF", country="CM",
                description="", metadata=None, idempotency_key=None):
        body = {
            "operator": operator,
            "country": country,
            "phone_number": phone_number,
            "amount": int(amount),
            "currency": currency,
        }
        if description:
            body["description"] = description
        if metadata:
            body["metadata"] = metadata
        reponse = self._requests.post(
            f"{self.base}/api/v1/payin/mobile-money",
            headers=self._headers(idempotency_key or str(uuid.uuid4())),
            json=body,
            timeout=30,
        )
        return self._json_ou_erreur(reponse)

    def statut_paiement(self, reference):
        reponse = self._requests.get(
            f"{self.base}/v1/payments/{reference}",
            headers=self._headers(),
            timeout=20,
        )
        return self._json_ou_erreur(reponse)

    def _json_ou_erreur(self, reponse):
        try:
            data = reponse.json()
        except ValueError:
            data = {}
        if reponse.status_code >= 400 or (isinstance(data, dict) and data.get("error")):
            raise HRSkillsPayError(
                data.get("error", f"HTTP_{reponse.status_code}"),
                data.get("message", (reponse.text or "")[:200]),
                data.get("details"),
                reponse.status_code,
            )
        return data


def get_client():
    if getattr(settings, "HRSKILLS_MOCK", True) or not settings.HRSKILLS_KEY_A:
        return GatewayMock()
    return GatewayHRSkills()
