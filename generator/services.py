from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from django.conf import settings

from .models import GenerationRequest, ModelGeneration
from .providers import MODEL_CATALOG, ProviderError, ReplicateProvider

TERMINAL_STATES = {"succeeded", "failed", "canceled"}


def generate_model_images(prompt: str, selected_models: list[str], image_count: int = 3) -> list[dict[str, str]]:
    """Compatibility helper for the legacy form-based generation flow.

    This keeps the older Django views working while still using the same
    allowlisted Replicate provider logic used elsewhere in the app.
    """
    provider = ReplicateProvider()
    generated: list[dict[str, str]] = []

    for model_key in selected_models:
        model_entry = MODEL_CATALOG.get(model_key, {})
        if not model_entry:
            continue
        try:
            prediction = provider.create_prediction(model_key, prompt)
        except ProviderError:
            continue

        output_urls = prediction.get("output_urls") or []
        if not output_urls:
            continue

        url = output_urls[0]
        generated.append({
            "model_name": model_entry.get("name", model_key),
            "image_path": url,
            "image_url": url,
        })

        if len(generated) >= max(1, image_count):
            break

    return generated


def start_generation(record: GenerationRequest) -> None:
    """Start one provider prediction per selected model concurrently."""
    provider = ReplicateProvider()
    generations = list(record.model_generations.all())
    with ThreadPoolExecutor(max_workers=min(len(generations), 4) or 1) as pool:
        futures = {
            pool.submit(provider.create_prediction, item.model_key, record.prompt): item
            for item in generations
        }
        for future in as_completed(futures):
            item = futures[future]
            try:
                prediction = future.result()
            except ProviderError as exc:
                item.status = "failed"
                item.error = str(exc)
            except Exception:
                item.status = "failed"
                item.error = "Unexpected error starting this model. Please retry."
            else:
                item.prediction_id = prediction["id"]
                item.status = prediction["status"]
                item.output_urls = prediction["output_urls"]
                item.error = prediction["error"]
            item.save(update_fields=["prediction_id", "status", "output_urls", "error", "updated_at"])
    refresh_request_status(record)


def refresh_generation(record: GenerationRequest) -> None:
    provider = ReplicateProvider()
    for item in record.model_generations.exclude(status__in=TERMINAL_STATES).exclude(prediction_id=""):
        try:
            prediction = provider.get_prediction(item.prediction_id)
        except ProviderError as exc:
            item.error = str(exc)
        except Exception:
            item.error = "Generation status is temporarily unavailable; retrying."
        else:
            item.status = prediction["status"]
            item.output_urls = prediction["output_urls"]
            item.error = prediction["error"]
        item.save(update_fields=["status", "output_urls", "error", "updated_at"])
    refresh_request_status(record)


def refresh_request_status(record: GenerationRequest) -> None:
    states = list(record.model_generations.values_list("status", flat=True))
    if states and all(state in TERMINAL_STATES for state in states):
        record.status = "succeeded" if any(state == "succeeded" for state in states) else "failed"
    elif states:
        record.status = "processing"
    else:
        record.status = "failed"
    record.save(update_fields=["status"])


def serialize_generation(record: GenerationRequest) -> dict[str, Any]:
    return {
        "id": str(record.public_id),
        "status": record.status,
        "prompt": record.prompt,
        "created_at": record.created_at.isoformat(),
        "models": [
            {
                "key": item.model_key,
                "name": item.model_name,
                "status": item.status,
                "images": item.output_urls,
                "error": item.error,
            }
            for item in record.model_generations.all()
        ],
    }


def rate_limit_per_hour() -> int:
    return max(1, int(getattr(settings, "RATE_LIMIT_PER_HOUR", 10)))
