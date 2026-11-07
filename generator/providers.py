from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import requests
from django.conf import settings


class ProviderError(Exception):
    """A safe, user-displayable provider failure."""


# Version-pinned Replicate models. The UI only sends these allowlisted keys;
# users cannot submit an arbitrary model or API URL.
MODEL_CATALOG: dict[str, dict[str, str]] = {
    "sdxl-lightning": {
        "name": "SDXL Lightning 4-Step",
        "id": "bytedance/sdxl-lightning-4step",
        "version": "5f24084160c9089501c1b3545d9be3c27883ae2239b6f412990e82d4a6210f8f",
        "description": "Fast SDXL image generation for rapid prompt comparisons.",
        "category": "Fast",
    },
    "flux-pro": {
        "name": "FLUX 1.1 Pro",
        "id": "black-forest-labs/flux-1.1-pro",
        "version": "609793a667ed94b210242837d3c3c9fc9a64ae93685f15d75002ba0ed9a97f2b",
        "description": "High-fidelity generation with strong prompt comprehension.",
        "category": "Photoreal",
    },
    "recraft-v3": {
        "name": "Recraft V3",
        "id": "recraft-ai/recraft-v3",
        "version": "9507e61ddace8b3a238371b17a61be203747c5081ea6070fecd3c40d27318922",
        "description": "Versatile image generation, including graphic and text-heavy styles.",
        "category": "Design",
    },
    "sd-3-5-large": {
        "name": "Stable Diffusion 3.5 Large",
        "id": "stability-ai/stable-diffusion-3.5-large",
        "version": "2fdf9488b53c1e0fd3aef7b477def1c00d1856a38466733711f9c769942598f5",
        "description": "Detailed outputs with strong composition and typography.",
        "category": "Open weights",
    },
}


class ReplicateProvider:
    API_URL = "https://api.replicate.com/v1/predictions"

    def __init__(self, token: str | None = None, timeout: int = 25):
        self.token = token or getattr(settings, "REPLICATE_API_TOKEN", "")
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        if not self.token:
            raise ProviderError("Image generation is not configured. Add REPLICATE_API_TOKEN to the server environment.")
        return {"Authorization": f"Token {self.token}", "Content-Type": "application/json"}

    def create_prediction(self, model_key: str, prompt: str) -> dict[str, Any]:
        model = MODEL_CATALOG[model_key]
        try:
            response = requests.post(
                self.API_URL,
                headers={**self._headers(), "Prefer": "wait=1"},
                json={"version": model["version"], "input": {"prompt": prompt}},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise ProviderError("Could not reach the image generation provider. Please try again.") from exc
        if not response.ok:
            raise ProviderError(self._provider_message(response))
        payload = response.json()
        if not payload.get("id"):
            raise ProviderError("The provider returned an invalid prediction response.")
        return self._normalize(payload)

    def get_prediction(self, prediction_id: str) -> dict[str, Any]:
        try:
            response = requests.get(
                f"{self.API_URL}/{prediction_id}",
                headers=self._headers(),
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise ProviderError("The generation status is temporarily unavailable.") from exc
        if not response.ok:
            raise ProviderError(self._provider_message(response))
        return self._normalize(response.json())

    @staticmethod
    def _provider_message(response: requests.Response) -> str:
        if response.status_code == 429:
            return "The image provider is rate limiting requests. Please wait and try again."
        if response.status_code in (401, 403):
            return "The server's image provider credentials were rejected."
        return f"The image provider could not process this request (HTTP {response.status_code})."

    @staticmethod
    def _normalize(payload: dict[str, Any]) -> dict[str, Any]:
        raw_output = payload.get("output")
        candidates = raw_output if isinstance(raw_output, list) else ([raw_output] if raw_output else [])
        urls = []
        for candidate in candidates:
            if not isinstance(candidate, str):
                continue
            parsed = urlparse(candidate)
            if parsed.scheme == "https" and parsed.netloc:
                urls.append(candidate)
        status = payload.get("status", "processing")
        return {
            "id": str(payload.get("id", "")),
            "status": status,
            "output_urls": urls,
            "error": "The provider reported that generation failed." if status == "failed" else "",
        }
