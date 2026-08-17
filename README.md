# Hitech Inventory & Cost-Code Control

A Django system for tracking warehouse/quarry stock, plant & equipment fuel and spares, and allocating material costs to project cost codes across multi-country operations (Nigeria, Togo, Benin).

## What it does

- **Stock ledger** — append-only transaction log (`stock`) is the single source of truth for where every unit of stock went and who pays for it. Corrections are reversing entries, never edits to a posted row, since the ledger doubles as the project's material-cost record.
- **Warehouses** (`warehouses`) — physical stock points modelled as a self-referencing hierarchy (country → project/site → store), so a central depot feeding several state depots feeding site stores is a natural shape, not a fixed-depth compromise.
- **Items** (`items`) — the catalog: aggregates (quarried material), fuel, spare parts, consumables, tools, each with a valuation method (weighted average or standard cost).
- **Fleet** (`fleet`) — plant/vehicle units that fuel and spares get issued against, tracked by hour meter or odometer.
- **Procurement** (`procurement`) — suppliers and purchasing, scoped by country.
- **Projects** (`projects`) — projects and their cost codes, the destination every stock movement gets allocated to.
- **Accounts** (`accounts`) — a custom user model with an organization-wide role (Administrator, Store Keeper, Quarry Manager, Fleet/Plant Manager, Procurement Officer, Cost Accountant/QS, Project Manager, Viewer). Which specific stores/projects a non-admin user can touch is scoped separately via `warehouses.StoreAssignment` and `projects.ProjectMembership`.
- **Audit** (`audit`) — an audit trail of the actions that matter (user/project/cost-code/store/item/equipment creation, work orders, quarry production).
- **API** — a DRF API with browsable schema/docs at `/api/schema/`, `/api/docs/` (Swagger), and `/api/redoc/`.

## Tech stack

- Django 5.1, PostgreSQL (via `psycopg`)
- Django REST Framework + drf-spectacular (OpenAPI schema)
- Celery + Redis (async tasks, result backend in the DB)
- Redis-backed cache
- pytest / pytest-django + factory-boy for testing

## Getting started

### Prerequisites

- Python 3.12+
- PostgreSQL
- Redis (native, or in WSL2 reachable via loopback on Windows)

### Setup

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash
# venv\Scripts\Activate.ps1    # PowerShell

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# then edit .env: set DJANGO_SECRET_KEY, DATABASE_URL, etc.

# Create the database (matching DATABASE_URL in .env), then:
python manage.py migrate
python manage.py createsuperuser

# Run the dev server
python manage.py runserver
```

The app is now at `http://127.0.0.1:8000/`, admin at `/admin/`, API docs at `/api/docs/`.

### Background tasks (Celery)

Requires Redis running at the URL configured by `CELERY_BROKER_URL`.

```bash
celery -A config worker -l info
```

Set `CELERY_TASK_ALWAYS_EAGER=True` in `.env` to run tasks synchronously without a worker (handy for local dev).

### Running tests

```bash
python manage.py test
```

## Configuration

Settings are split by environment:

- `config/settings/base.py` — shared settings
- `config/settings/dev.py` — local development (`DEBUG=True`, console email backend)
- `config/settings/prod.py` — production (HTTPS/HSTS enforcement, SMTP email, assumes a TLS-terminating reverse proxy)

Select one via `DJANGO_SETTINGS_MODULE` in `.env` (defaults to `config.settings.dev`).

Key environment variables (see `.env.example` for the full list):

| Variable | Purpose |
| --- | --- |
| `DJANGO_SETTINGS_MODULE` | Which settings module to load |
| `DJANGO_SECRET_KEY` | Django secret key |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hosts |
| `DATABASE_URL` | PostgreSQL connection string |
| `CELERY_BROKER_URL` / `REDIS_CACHE_URL` | Redis connections for Celery and cache (separate DB indexes) |
| `SUPPORTED_CURRENCIES` / `DEFAULT_CURRENCY` | Currencies transactions can post in (NGN, XOF) |
| `RATE_LIMIT_LOGIN_PER_MIN` / `RATE_LIMIT_API_GENERAL_PER_MIN` | Throttle rates for login and the general API |
