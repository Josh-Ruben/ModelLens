from django.urls import path

from .views import generate, home, results

urlpatterns = [
    path("", home, name="home"),
    path("generate/", generate, name="generate"),
    path("results/<int:request_id>/", results, name="results"),
]
