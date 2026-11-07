from django import forms


MODEL_CHOICES = [
    ("sdxl", "SDXL"),
    ("flux", "Flux"),
    ("dalle", "DALL·E"),
    ("midjourney", "Midjourney-like"),
]


class GenerationForm(forms.Form):
    prompt = forms.CharField(
        label="Prompt",
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": "Describe the scene, subject, style, and mood..."}),
        min_length=5,
    )
    selected_models = forms.MultipleChoiceField(
        label="Models to compare",
        choices=MODEL_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        initial=["sdxl", "flux", "dalle"],
    )
    image_count = forms.IntegerField(
        label="Images per model",
        min_value=1,
        max_value=4,
        initial=3,
    )
