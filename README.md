# ModelLens

**ModelLens** is a multi-model text-to-image comparison workbench. Submit one prompt to several version-pinned image models in parallel, follow each prediction independently, and inspect the outputs in a side-by-side board.

> ModelLens is an independent project. ModelLens is not affiliated with or endorsed by MIRAGE or the authors of the linked research project. This implementation follows its own Django-based architecture and does not copy MIRAGE's source code or model catalog wholesale.

## What works

- Real Replicate prediction creation and status polling; the API token stays on the server.
- Four allowlisted, version-pinned models; at most four models per comparison.
- Parallel model starts and independent per-model success/failure states.
- Persisted prompt/comparison history in Django's database.
- Responsive comparison board, image lightbox, and recent-run browsing.
- Prompt validation, per-IP hourly request throttling, HTTPS-only output URLs, and request-size limits.
- Django admin for inspecting runs and provider states.

## Stack

- Python 3.12+, Django 5.1, Requests
- Replicate predictions API
- SQLite for development; configure PostgreSQL and a shared cache for production
- Docker / Docker Compose

## Run locally

1. Create a Replicate API token at [Replicate](https://replicate.com/account/api-tokens).
2. Create and activate a virtual environment, then install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
   pip install -r requirements.txt
   ```
3. Set configuration (do not commit secrets):

   ```bash
   export REPLICATE_API_TOKEN="your-token"
   export DJANGO_SECRET_KEY="replace-with-a-long-random-secret"
   ```
4. Apply migrations and run the development server:

   ```bash
   python manage.py migrate
   python manage.py runserver
   ```
5. Visit http://127.0.0.1:8000/.

On Windows PowerShell, use `$env:REPLICATE_API_TOKEN="your-token"` and `$env:DJANGO_SECRET_KEY="..."`.

## Docker

Set `REPLICATE_API_TOKEN` and `DJANGO_SECRET_KEY` in the environment, then run:

```bash
docker compose up --build
```

The development compose setup uses SQLite and mounts the source tree. Do not use Django's development server or the checked-in development defaults as a production deployment configuration.

## Configuration

| Variable | Purpose | Default |
| --- | --- | --- |
| `REPLICATE_API_TOKEN` | Server-side Replicate credential (required for generation) | unset |
| `DJANGO_SECRET_KEY` | Django signing secret | development-only value |
| `DJANGO_DEBUG` | Django debug mode | `1` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hosts | localhost addresses |
| `RATE_LIMIT_PER_HOUR` | Soft per-IP generation start limit | `10` |

Never expose the Replicate token in browser JavaScript or commit it to the repository. Each selected model incurs provider usage/cost. The app warns users about provider costs; deployment owners should set billing limits and operate a shared cache (such as Redis) for effective rate limiting across processes. The default local-memory cache is not a distributed limiter.

## Models

The model catalog is maintained in `generator/providers.py`, where each entry pins a Replicate model/version pair. Change the allowlist there after checking the provider's current model schema and version. The app submits only a `prompt` to each model and relies on that version's defaults; model-specific parameters and batching should only be added with schema-aware validation.

## Architecture

- `generator/providers.py`: provider API client, model allowlist, response normalization.
- `generator/services.py`: concurrent prediction starts, polling updates, request status aggregation.
- `generator/views.py`: JSON endpoints, validation, throttling, history.
- `generator/models.py`: persisted comparison and per-model generation records.
- `static/generator/`: accessible, responsive UI and asynchronous polling client.

Generation is asynchronous at the provider level: the POST endpoint starts predictions and returns their current state, while the browser polls the status endpoint. The web server does not hold a request open while diffusion runs. The current version polls from the client rather than running a separate worker; production-scale deployments should move polling/webhooks to a durable queue and use a shared database/cache.

## Production checklist

- Set `DJANGO_DEBUG=0`, a strong `DJANGO_SECRET_KEY`, and exact `DJANGO_ALLOWED_HOSTS`.
- Use PostgreSQL, HTTPS, secure cookies, a shared Redis cache, and a production WSGI server.
- Configure static/media storage and retention policies; provider output URLs may be temporary.
- Add authentication/ownership controls before exposing private prompt history to multiple users. Current history is shared by design for a single-user demo and should not be treated as private.
- Set provider budget limits and monitor provider failures, latency, and usage.
- Consider provider webhooks or a durable worker for robust long-running prediction updates.

## Tests

```bash
python manage.py test
python manage.py check
```

## License

MIT. See [LICENSE](LICENSE).
