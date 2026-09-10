"""Panier stocke en session.

Contrainte du cahier des charges : un panier ne contient des articles que d'une
seule boutique a la fois (§5.1.3 / §8.2).
"""
from admin.produits.models import Produit, VarianteProduit

CLE_SESSION = "panier"


class PanierAutreBoutique(Exception):
    """Tentative d'ajout d'un produit d'une autre boutique que celle du panier."""


def _cle(produit_id, variante_id):
    return f"{produit_id}:{variante_id or 0}"


class Panier:
    def __init__(self, request):
        self.session = request.session
        self.data = self.session.get(CLE_SESSION) or {"boutique_id": None, "lignes": {}}

    # -- persistance ----------------------------------------------------
    def _sauver(self):
        self.session[CLE_SESSION] = self.data
        self.session.modified = True

    # -- lecture ------------------------------------------------------
    @property
    def boutique_id(self):
        return self.data.get("boutique_id")

    def nb_articles(self):
        return sum(self.data["lignes"].values())

    def _resoudre(self):
        """Recharge produits / variantes et purge les lignes devenues invalides."""
        lignes, modifie = [], False
        for cle, quantite in list(self.data["lignes"].items()):
            pid, vid = (int(x) for x in cle.split(":"))
            produit = Produit.objects.filter(pk=pid).first()
            variante = VarianteProduit.objects.filter(pk=vid).first() if vid else None
            if produit is None or (vid and variante is None):
                del self.data["lignes"][cle]
                modifie = True
                continue
            prix = variante.prix_effectif if variante else produit.prix
            stock = variante.stock if variante else produit.stock
            if quantite > stock:
                quantite = stock
                self.data["lignes"][cle] = quantite
                modifie = True
            if quantite <= 0:
                del self.data["lignes"][cle]
                modifie = True
                continue
            lignes.append({
                "cle": cle,
                "produit": produit,
                "variante": variante,
                "quantite": quantite,
                "prix_unitaire": prix,
                "sous_total": prix * quantite,
                "stock": stock,
            })
        if not self.data["lignes"]:
            self.data["boutique_id"] = None
        if modifie:
            self._sauver()
        return lignes

    def lignes(self):
        return self._resoudre()

    def total(self):
        return sum(ligne["sous_total"] for ligne in self._resoudre())

    # -- ecriture ---------------------------------------------------
    def ajouter(self, produit, variante, quantite):
        if self.data["lignes"] and self.boutique_id != produit.boutique_id:
            raise PanierAutreBoutique()
        quantite = max(1, int(quantite))
        stock = variante.stock if variante else produit.stock
        cle = _cle(produit.id, variante.id if variante else 0)
        nouveau = min(self.data["lignes"].get(cle, 0) + quantite, stock)
        if nouveau <= 0:
            return
        self.data["lignes"][cle] = nouveau
        self.data["boutique_id"] = produit.boutique_id
        self._sauver()

    def modifier(self, cle, quantite):
        quantite = int(quantite)
        if cle not in self.data["lignes"]:
            return
        if quantite <= 0:
            self.retirer(cle)
            return
        pid, vid = (int(x) for x in cle.split(":"))
        if vid:
            v = VarianteProduit.objects.filter(pk=vid).first()
            stock = v.stock if v else 0
        else:
            p = Produit.objects.filter(pk=pid).first()
            stock = p.stock if p else 0
        self.data["lignes"][cle] = min(quantite, stock)
        if self.data["lignes"][cle] <= 0:
            self.retirer(cle)
            return
        self._sauver()

    def retirer(self, cle):
        if cle in self.data["lignes"]:
            del self.data["lignes"][cle]
            if not self.data["lignes"]:
                self.data["boutique_id"] = None
            self._sauver()

    def vider(self):
        self.data = {"boutique_id": None, "lignes": {}}
        self._sauver()
