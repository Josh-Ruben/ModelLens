from django.urls import path

from .views import generate, health, home, results

urlpatterns = [
    path("", home, name="home"),
    path("health/", health, name="health"),
    path("generate/", generate, name="generate"),
    path("results/<int:request_id>/", results, name="results"),
]
