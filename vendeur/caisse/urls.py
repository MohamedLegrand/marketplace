from django.urls import path

from . import views

app_name = "caisse_vendeur"

urlpatterns = [
    path("", views.rapport, name="rapport"),
    path("pdf/", views.rapport_pdf, name="rapport_pdf"),
]
