from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="GenerationRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("prompt", models.TextField()),
                ("selected_models", models.JSONField(blank=True, default=list)),
                ("image_count", models.PositiveIntegerField(default=3)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="GeneratedImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("model_name", models.CharField(max_length=100)),
                ("image_path", models.CharField(max_length=255)),
                ("image_url", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("request", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="images", to="generator.generationrequest")),
            ],
        ),
    ]
