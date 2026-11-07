from django.contrib import admin
from .models import GeneratedImage, GenerationRequest, ModelGeneration


class ModelGenerationInline(admin.TabularInline):
    model = ModelGeneration
    extra = 0
    readonly_fields = ("model_key", "model_name", "prediction_id", "status", "error", "created_at", "updated_at")


@admin.register(GenerationRequest)
class GenerationRequestAdmin(admin.ModelAdmin):
    list_display = ("public_id", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("prompt",)
    readonly_fields = ("public_id", "created_at")
    inlines = [ModelGenerationInline]


@admin.register(GeneratedImage)
class GeneratedImageAdmin(admin.ModelAdmin):
    list_display = ("model_name", "request", "created_at")
