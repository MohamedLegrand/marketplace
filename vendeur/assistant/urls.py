from django.urls import path

from . import views

app_name = "assistant_vendeur"

urlpatterns = [
    path("", views.chat, name="chat"),
]
