from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    dependencies = [("generator", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="generationrequest",
            name="public_id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AddField(
            model_name="generationrequest",
            name="status",
            field=models.CharField(choices=[("queued", "Queued"), ("processing", "Processing"), ("succeeded", "Succeeded"), ("failed", "Failed")], default="queued", max_length=20),
        ),
        migrations.CreateModel(
            name="ModelGeneration",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("model_key", models.CharField(max_length=64)),
                ("model_name", models.CharField(max_length=120)),
                ("prediction_id", models.CharField(blank=True, max_length=128)),
                ("status", models.CharField(choices=[("queued", "Queued"), ("starting", "Starting"), ("processing", "Processing"), ("succeeded", "Succeeded"), ("failed", "Failed"), ("canceled", "Canceled")], default="queued", max_length=20)),
                ("output_urls", models.JSONField(blank=True, default=list)),
                ("error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("request", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="model_generations", to="generator.generationrequest")),
            ],
            options={"ordering": ["created_at", "id"]},
        ),
        migrations.AddConstraint(
            model_name="modelgeneration",
            constraint=models.UniqueConstraint(fields=("request", "model_key"), name="unique_model_per_generation_request"),
        ),
    ]
