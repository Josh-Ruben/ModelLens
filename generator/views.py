import json
from concurrent.futures import ThreadPoolExecutor

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from .models import GenerationRequest, ModelGeneration
from .providers import MODEL_CATALOG, ProviderError
from .services import rate_limit_per_hour, refresh_generation, serialize_generation, start_generation


def home(request: HttpRequest) -> HttpResponse:
    models = [
        {"key": key, "name": value["name"], "description": value["description"], "category": value["category"]}
        for key, value in MODEL_CATALOG.items()
    ]
    return render(request, "generator/home.html", {"models_json": json.dumps(models)})


@require_POST
def create_generation(request: HttpRequest) -> JsonResponse:
    if not getattr(settings, "REPLICATE_API_TOKEN", ""):
        return JsonResponse({"error": "Image generation is not configured on this server."}, status=503)

    client_ip = request.META.get("REMOTE_ADDR", "unknown")
    bucket = int(__import__("time").time() // 3600)
    cache_key = f"modellens:generation-rate:{client_ip}:{bucket}"
    if not cache.add(cache_key, 1, timeout=3700):
        try:
            count = cache.incr(cache_key)
        except ValueError:
            cache.set(cache_key, 1, timeout=3700)
            count = 1
    else:
        count = 1
    limit = rate_limit_per_hour()
    if count > limit:
        return JsonResponse({"error": f"Rate limit reached ({limit} generations per hour). Try again later."}, status=429)

    try:
        payload = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Request body must be valid JSON."}, status=400)
    prompt = payload.get("prompt")
    selected_models = payload.get("models")
    if not isinstance(prompt, str) or not 5 <= len(prompt.strip()) <= 2000:
        return JsonResponse({"error": "Prompt must contain between 5 and 2,000 characters."}, status=400)
    if not isinstance(selected_models, list) or not 1 <= len(selected_models) <= 4:
        return JsonResponse({"error": "Select between 1 and 4 models."}, status=400)
    if len(set(selected_models)) != len(selected_models) or any(key not in MODEL_CATALOG for key in selected_models):
        return JsonResponse({"error": "One or more selected models are invalid."}, status=400)

    record = GenerationRequest.objects.create(
        prompt=prompt.strip(),
        selected_models=selected_models,
        image_count=1,
        status="queued",
    )
    ModelGeneration.objects.bulk_create([
        ModelGeneration(
            request=record,
            model_key=key,
            model_name=MODEL_CATALOG[key]["name"],
            status="queued",
        )
        for key in selected_models
    ])
    try:
        start_generation(record)
    except ProviderError as exc:
        record.status = "failed"
        record.save(update_fields=["status"])
        return JsonResponse({"error": str(exc)}, status=502)
    record.refresh_from_db()
    return JsonResponse(serialize_generation(record), status=201)


@require_GET
def generation_status(request: HttpRequest, public_id: str) -> JsonResponse:
    record = get_object_or_404(GenerationRequest, public_id=public_id)
    if record.status not in ("succeeded", "failed"):
        refresh_generation(record)
        record.refresh_from_db()
    return JsonResponse(serialize_generation(record))


@require_GET
def history(request: HttpRequest) -> JsonResponse:
    records = GenerationRequest.objects.order_by("-created_at")[:20]
    return JsonResponse({"items": [serialize_generation(record) for record in records]})
