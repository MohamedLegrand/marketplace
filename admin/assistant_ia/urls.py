from django.urls import path

from . import views

app_name = "assistant_admin"

urlpatterns = [
    path("", views.analyse, name="analyse"),
]
