from django.db import models


class GenerationRequest(models.Model):
    prompt = models.TextField()
    selected_models = models.JSONField(default=list, blank=True)
    image_count = models.PositiveIntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)

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
