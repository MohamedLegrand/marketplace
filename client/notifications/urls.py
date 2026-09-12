from django.urls import path

from . import views

app_name = "notifications_client"

urlpatterns = [
    path("", views.liste, name="liste"),
    path("<int:pk>/", views.suivre, name="suivre"),
]
