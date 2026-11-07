from django.http import JsonResponse
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

from .forms import GenerationForm
from .models import GeneratedImage, GenerationRequest
from .services import generate_model_images


def home(request: HttpRequest) -> HttpResponse:
    form = GenerationForm()
    return render(request, "generator/home.html", {"form": form})


def health(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


def generate(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return HttpResponse(status=405)

    form = GenerationForm(request.POST)
    if not form.is_valid():
        return render(request, "generator/home.html", {"form": form, "errors": form.errors})

    prompt = form.cleaned_data["prompt"]
    selected_models = form.cleaned_data["selected_models"] or ["sdxl", "flux", "dalle"]
    image_count = form.cleaned_data["image_count"]

    request_record = GenerationRequest.objects.create(
        prompt=prompt,
        selected_models=selected_models,
        image_count=image_count,
    )

    generated = generate_model_images(prompt, selected_models, image_count)
    for item in generated:
        GeneratedImage.objects.create(
            request=request_record,
            model_name=item["model_name"],
            image_path=item["image_path"],
            image_url=item["image_url"],
        )

    return render(request, "generator/results.html", {"record": request_record, "images": request_record.images.all().order_by("model_name", "created_at")})


def results(request: HttpRequest, request_id: int) -> HttpResponse:
    record = GenerationRequest.objects.get(pk=request_id)
    images = record.images.all().order_by("model_name", "created_at")
    return render(request, "generator/results.html", {"record": record, "images": images})
