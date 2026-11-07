from django.db import models
import uuid


class GenerationRequest(models.Model):
    STATUS_CHOICES = [
        ("queued", "Queued"),
        ("processing", "Processing"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
    ]

    prompt = models.TextField()
    selected_models = models.JSONField(default=list, blank=True)
    image_count = models.PositiveIntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued")

    def __str__(self):
        return self.prompt[:80]


class GeneratedImage(models.Model):
    request = models.ForeignKey(GenerationRequest, related_name="images", on_delete=models.CASCADE)
    model_name = models.CharField(max_length=100)
    image_path = models.CharField(max_length=255)
    image_url = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.model_name} - {self.request.pk}"


class ModelGeneration(models.Model):
    STATUS_CHOICES = [
        ("queued", "Queued"),
        ("starting", "Starting"),
        ("processing", "Processing"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
        ("canceled", "Canceled"),
    ]

    request = models.ForeignKey(GenerationRequest, related_name="model_generations", on_delete=models.CASCADE)
    model_key = models.CharField(max_length=64)
    model_name = models.CharField(max_length=120)
    prediction_id = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued")
    output_urls = models.JSONField(default=list, blank=True)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(fields=["request", "model_key"], name="unique_model_per_generation_request")
        ]

    def __str__(self):
        return f"{self.model_name} ({self.status})"
