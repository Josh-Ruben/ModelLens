# Production deployment baseline: Django + Postgres + Redis + Gunicorn + Docker Compose

ModelLens includes a one-command Docker Compose setup for a production-style deployment with:
- Django + Gunicorn web server
- PostgreSQL database
- Redis for caching / job broker
- health endpoint
- secure production settings

## One-click setup

```bash
cp .env.example .env
# edit .env with strong secrets and your Replicate token

docker compose up --build -d
```

Then verify:

```bash
curl http://localhost:8000/health/
```

## Important notes

- Use real PostgreSQL and Redis credentials in `.env`, not the defaults.
- Set `DJANGO_SECRET_KEY` to a long random secret.
- Set `DJANGO_ALLOWED_HOSTS` to your real hostnames.
- Keep `REPLICATE_API_TOKEN` on the server only.
- Put a TLS reverse proxy in front of the app before public exposure.
- Do not expose PostgreSQL or Redis to the internet.

## Production hardening checklist

- set `DJANGO_DEBUG=0`
- configure HTTPS and a real domain
- enable backups for Postgres
- monitor worker queue and provider cost
- keep `.env` out of version control
