from django.urls import path

from .views import create_generation, generation_status, history, home

urlpatterns = [
    path("", home, name="home"),
    path("api/generations/", create_generation, name="create_generation"),
    path("api/generations/<uuid:public_id>/", generation_status, name="generation_status"),
    path("api/history/", history, name="generation_history"),
]
