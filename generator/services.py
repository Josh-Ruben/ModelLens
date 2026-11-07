from __future__ import annotations

import hashlib
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from django.conf import settings

MODEL_META = {
    "sdxl": {"label": "SDXL", "colors": ("#8b5cf6", "#f472b6")},
    "flux": {"label": "Flux", "colors": ("#14b8a6", "#34d399")},
    "dalle": {"label": "DALL·E", "colors": ("#f59e0b", "#ef4444")},
    "midjourney": {"label": "Midjourney-like", "colors": ("#3b82f6", "#8b5cf6")},
}


class BaseImageProvider(ABC):
    """Contract for model providers used by ModelLens."""

    name: str = "base"

    @abstractmethod
    def generate(self, *, prompt: str, model_key: str, output_path: Path, seed: int, index: int) -> dict[str, Any]:
        raise NotImplementedError


class DemoImageProvider(BaseImageProvider):
    """Fallback provider for local development and demos. It generates SVG mock outputs."""

    name = "demo"

    def generate(self, *, prompt: str, model_key: str, output_path: Path, seed: int, index: int) -> dict[str, Any]:
        output_path.write_text(build_svg(model_key, prompt, seed), encoding="utf-8")
        return {
            "provider": self.name,
            "model_key": model_key,
            "seed": seed,
            "index": index,
            "path": str(output_path),
        }


class ReplicateProvider(BaseImageProvider):
    """Real provider adapter for future Replicate integration."""

    name = "replicate"

    def generate(self, *, prompt: str, model_key: str, output_path: Path, seed: int, index: int) -> dict[str, Any]:
        token = os.getenv("REPLICATE_API_TOKEN")
        if not token:
            raise RuntimeError("REPLICATE_API_TOKEN is not configured.")

        # This is intentionally left as a provider-ready skeleton for the next phase.
        # The actual API call can be layered in here when credentials are available.
        output_path.write_text(build_svg(model_key, prompt, seed), encoding="utf-8")
        return {
            "provider": self.name,
            "model_key": model_key,
            "seed": seed,
            "index": index,
            "path": str(output_path),
        }


class OpenAIProvider(BaseImageProvider):
    """Provider-ready adapter for OpenAI-compatible image services."""

    name = "openai"

    def generate(self, *, prompt: str, model_key: str, output_path: Path, seed: int, index: int) -> dict[str, Any]:
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        output_path.write_text(build_svg(model_key, prompt, seed), encoding="utf-8")
        return {
            "provider": self.name,
            "model_key": model_key,
            "seed": seed,
            "index": index,
            "path": str(output_path),
        }


def get_provider() -> BaseImageProvider:
    provider_name = os.getenv("MODEL_LENS_PROVIDER", "demo").strip().lower()
    providers = {
        "demo": DemoImageProvider(),
        "replicate": ReplicateProvider(),
        "openai": OpenAIProvider(),
    }
    provider = providers.get(provider_name)
    if provider is None:
        raise ValueError(f"Unsupported MODEL_LENS_PROVIDER: {provider_name}")
    return provider


def _slugify(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in ("-", "_") else "-" for ch in value.lower())
    cleaned = cleaned.strip("-")
    return cleaned[:80] or "prompt"


def _hash_seed(value: str) -> int:
    return int(hashlib.md5(value.encode("utf-8")).hexdigest()[:8], 16)


def build_svg(model_key: str, prompt: str, seed: int) -> str:
    meta = MODEL_META[model_key]
    label = meta["label"]
    start_color, end_color = meta["colors"]
    prompt_lines = [prompt[i : i + 28] for i in range(0, len(prompt), 28)]
    if not prompt_lines:
        prompt_lines = ["Untitled prompt"]
    lines = "\n".join(
        f"<tspan x='40' dy='{22 * idx}'>{line}</tspan>" for idx, line in enumerate(prompt_lines[:6])
    )
    return f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 900" width="1200" height="900">
      <defs>
        <linearGradient id="bg-{seed}" x1="0%" x2="100%" y1="0%" y2="100%">
          <stop offset="0%" stop-color="{start_color}"/>
          <stop offset="100%" stop-color="{end_color}"/>
        </linearGradient>
      </defs>
      <rect width="1200" height="900" fill="url(#bg-{seed})"/>
      <circle cx="960" cy="170" r="150" fill="rgba(255,255,255,0.12)"/>
      <circle cx="260" cy="700" r="200" fill="rgba(255,255,255,0.10)"/>
      <rect x="50" y="60" width="430" height="70" rx="18" fill="rgba(15,23,42,0.28)"/>
      <text x="80" y="106" font-family="Arial, sans-serif" font-size="30" font-weight="700" fill="#ffffff">ModelLens / {label}</text>
      <rect x="60" y="160" width="1080" height="610" rx="26" fill="rgba(15,23,42,0.18)" stroke="rgba(255,255,255,0.3)"/>
      <g>
        <path d="M150 620 C 260 470, 420 470, 540 620 S 820 770, 1030 620" fill="none" stroke="rgba(255,255,255,0.32)" stroke-width="10" stroke-linecap="round"/>
        <path d="M180 624 L 260 540 L 380 620 L 480 512 L 630 640 L 730 560 L 900 680 L 1010 540" fill="none" stroke="rgba(255,255,255,0.8)" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
      </g>
      <text x="80" y="210" font-family="Arial, sans-serif" font-size="26" fill="#e2e8f0">Prompt</text>
      <text x="80" y="260" font-family="Arial, sans-serif" font-size="28" font-weight="600" fill="#ffffff">{lines}</text>
      <text x="80" y="740" font-family="Arial, sans-serif" font-size="24" fill="#cffafe">Seed: {seed}</text>
    </svg>
    """


def generate_model_images(prompt: str, selected_models: list[str], image_count: int) -> list[dict[str, Any]]:
    """Generates image payloads using a provider backend. At the moment the demo provider produces SVGs."""
    provider = get_provider()
    results: list[dict[str, Any]] = []
    base_dir = Path(settings.MEDIA_ROOT) / "generated"
    base_dir.mkdir(parents=True, exist_ok=True)

    for model_key in selected_models:
        model_config = MODEL_META.get(model_key)
        if not model_config:
            continue

        for index in range(image_count):
            seed = _hash_seed(f"{prompt}:{model_key}:{index}")
            filename = f"{_slugify(prompt)}_{model_key}_{index}_{seed}.svg"
            image_path = base_dir / filename
            provider.generate(prompt=prompt, model_key=model_key, output_path=image_path, seed=seed, index=index)
            results.append(
                {
                    "model_name": model_config["label"],
                    "filename": filename,
                    "image_path": str(image_path),
                    "image_url": f"/media/generated/{filename}",
                }
            )
    return results
