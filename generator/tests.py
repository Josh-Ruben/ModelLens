from django.test import TestCase, override_settings
from django.urls import reverse
from unittest.mock import patch

from .models import GenerationRequest, ModelGeneration
from .providers import MODEL_CATALOG, ProviderError, ReplicateProvider


class ReplicateProviderTests(TestCase):
    @override_settings(REPLICATE_API_TOKEN="test-token")
    @patch("generator.providers.requests.post")
    def test_create_prediction_uses_allowlisted_version_and_prompt(self, post):
        post.return_value.ok = True
        post.return_value.json.return_value = {"id": "prediction-123", "status": "starting", "output": None}
        result = ReplicateProvider().create_prediction("flux-pro", "A quiet mountain lake")
        self.assertEqual(result["id"], "prediction-123")
        self.assertEqual(result["status"], "starting")
        self.assertEqual(post.call_args.kwargs["json"], {
            "version": MODEL_CATALOG["flux-pro"]["version"],
            "input": {"prompt": "A quiet mountain lake"},
        })

    @override_settings(REPLICATE_API_TOKEN="")
    def test_missing_token_is_reported_without_network_call(self):
        with self.assertRaises(ProviderError):
            ReplicateProvider().create_prediction("flux-pro", "A quiet mountain lake")

    def test_normalize_rejects_non_https_output_urls(self):
        result = ReplicateProvider._normalize({
            "id": "prediction-1", "status": "succeeded",
            "output": ["https://images.example/output.png", "http://unsafe.example/image.png", "javascript:alert(1)"],
        })
        self.assertEqual(result["output_urls"], ["https://images.example/output.png"])


class GenerationApiTests(TestCase):
    @override_settings(REPLICATE_API_TOKEN="test-token", RATE_LIMIT_PER_HOUR=10)
    @patch("generator.views.start_generation")
    def test_create_validates_models_and_returns_async_job(self, start):
        start.side_effect = lambda record: None
        response = self.client.post(
            reverse("create_generation"),
            data='{"prompt":"A calm mountain lake at sunrise","models":["flux-pro","sdxl-lightning"]}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["status"], "queued")
        self.assertEqual(len(body["models"]), 2)
        self.assertTrue(GenerationRequest.objects.filter(public_id=body["id"]).exists())

    @override_settings(REPLICATE_API_TOKEN="test-token")
    def test_rejects_unlisted_models(self):
        response = self.client.post(
            reverse("create_generation"),
            data='{"prompt":"A calm mountain lake at sunrise","models":["attacker/model"]}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    @override_settings(REPLICATE_API_TOKEN="")
    def test_requires_server_provider_configuration(self):
        response = self.client.post(
            reverse("create_generation"),
            data='{"prompt":"A calm mountain lake at sunrise","models":["flux-pro"]}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 503)

    def test_history_does_not_expose_provider_prediction_ids(self):
        record = GenerationRequest.objects.create(prompt="A mountain scene", selected_models=["flux-pro"])
        ModelGeneration.objects.create(
            request=record, model_key="flux-pro", model_name="FLUX 1.1 Pro", prediction_id="secret-provider-id"
        )
        response = self.client.get(reverse("generation_history"))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("secret-provider-id", response.content.decode())
