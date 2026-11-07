from django.http import HttpRequest
from django.urls import reverse
from django.test import Client

from .models import GenerationRequest


def test_home_page_loads(client: Client) -> None:
    response = client.get(reverse("home"))
    assert response.status_code == 200
    assert b"ModelLens" in response.content


def test_generation_creates_result(client: Client) -> None:
    response = client.post(
        reverse("generate"),
        {
            "prompt": "A futuristic city at sunset with neon reflections",
            "selected_models": ["sdxl", "flux"],
            "image_count": 2,
        },
    )
    assert response.status_code == 302
    assert GenerationRequest.objects.count() == 1
