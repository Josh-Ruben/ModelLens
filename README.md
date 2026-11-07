# ModelLens

ModelLens is a text-to-image comparison platform for exploring prompts across multiple image generation models and comparing the outputs side by side.

## Features

- Prompt-driven image generation workflow
- Compare results across multiple model backends
- Lightweight Django app with a clean modern interface
- Dockerized local setup
- AWS-ready architecture for future deployment

## Tech stack

- Django
- SQLite for local dev
- Pillow
- Docker
- AWS-ready storage patterns for S3, DynamoDB and Lambda integration

## Quick start

### Prerequisites

- Python 3.12+
- Docker and Docker Compose (optional)

### Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/

### Docker

```bash
docker compose up --build
```

## Project structure

```text
model_lens_project/
    settings.py
    urls.py
    wsgi.py
    asgi.py
generator/
    migrations/
    templates/
    static/
    services.py
    views.py
    forms.py
    models.py
```

## Roadmap

- Add real image model providers (Replicate, OpenAI, Stability, local backends)
- Add asynchronous job processing
- Add image comparison gallery with scoring
- Add user accounts and saved prompts
- Add AWS deployment skeleton for S3 and DynamoDB

## License

MIT
