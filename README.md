# BusinessOS

BusinessOS is a modular Django business application. Phase 0 provides the complete Core Foundation
v1, and Phase 1 adds the accepted Party and variant-first Catalog modules without coupling domain
services to Django requests.

## Requirements

- Python 3.13+
- PostgreSQL 17 (or Docker Desktop)

## Start with Docker

```bash
cp .env.example .env
docker compose up --build
```

The application is available at <http://localhost:8000> and PostgreSQL data is retained in the `postgres_data` volume.

Create an administrator in another terminal:

```bash
docker compose exec web python manage.py createsuperuser
```

Optionally load the small idempotent starter set of countries, currencies, languages, and units:

```bash
docker compose exec web python manage.py seed_reference_data
```

Then sign in at <http://localhost:8000/login/>. Organization and access records can initially be managed through <http://localhost:8000/admin/>.

The Django admin is deliberately restricted to active superusers because it is a deployment-wide maintenance surface, not a company-scoped operational interface. Staff users with model permissions cannot enter it.

## Local development

Create a PostgreSQL database and export the variables shown in `.env.example`, then:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements/development.lock
python manage.py migrate
python manage.py seed_reference_data
python manage.py createsuperuser
python manage.py runserver
```

When shared template utility classes change, rebuild the committed Tailwind stylesheet:

```bash
npm ci
npm run build:css
```

Normal development and production settings use PostgreSQL. Test settings use an isolated in-memory SQLite database so unit tests do not depend on a running service.

## Quality checks

```bash
pytest
ruff check .
python manage.py check
python manage.py makemigrations --check
```

## Architecture at a glance

- `businessos/core/identity` — email-based Django user
- `businessos/core/reference` — small global reference tables
- `businessos/core/organization` — company, branch, and warehouse scope
- `businessos/core/access` — explicit per-user organization grants and request adapter
- `businessos/core/modules` — manifest validation and enabled-module registry
- `businessos/core/common` — UUID/timestamp models and framework-neutral `BusinessContext`
- `businessos/modules/party` — company-scoped person/organization identity, contacts, and addresses
- `businessos/modules/catalog` — products and concrete sellable/purchasable ProductVariant identity
- `businessos/modules` — standard business modules; Phase 2 modules are not adopted on this candidate
- `businessos/extensions` — deployment-specific extensions

Read `AGENTS.md` and the documents under `docs/architecture/` before changing core contracts or adding modules.

Foundation security and ownership semantics are recorded in ADR 0001 and ADR 0009. The
`gate3-canonical-reconstruction` branch is a review candidate only; canonical `main` has not been
cut over.
