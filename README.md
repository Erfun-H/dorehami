<p align="center">
  <strong>
    <span>English</span> | <a href="README.fa.md">فارسی</a>
  </strong>
</p>

# Dorehami

A web app for coordinating get-togethers: the host creates a get-together, shares the invitation link with friends, everyone proposes dates and times, they agree on the suggestions, and finally the host locks in the final time.

## Features

- **User account** — sign up and login with email and password.
- **Create a get-together** — a title and optional details; each get-together gets an invitation link with a random token.
- **Join via invitation link** — a signed-in user who opens the valid link of an active get-together is added as a participant.
- **Date suggestions** — participants submit date/time suggestions with the Jalali datepicker; each suggestion can only be edited by its creator.
- **Agreement** — every participant can agree with any suggestion, or withdraw their agreement.
- **Finalize** — only the host can finalize a get-together, and only when at least one agreement has been made by someone other than themselves. After finalize, all suggestions and agreements are locked and the invitation link no longer accepts new members.

## Technologies

- Python 3.12 and Django 6
- PostgreSQL with psycopg 3
- django-jalali for storing and displaying Jalali dates (`jDateField` and the `jformat` template filter) + the `jalali-datepicker` widget
- Tailwind CSS 4 — source in `src/theme/`, built output in `src/static/css/app.css`
- Ruff for lint and format, pytest and pytest-django for tests

## Setup

Prerequisites: Python 3.12 and a running PostgreSQL.

```bash
# virtualenv and installing dependencies
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

# create the database
createdb dorehami

# environment variables
cp .env.example .env.dev   # adjust the values for your system
set -a; source .env.dev; set +a

# apply migrations and start the server
python src/manage.py migrate
python src/manage.py runserver
```

The app runs at `http://127.0.0.1:8000/`.

If you want to rebuild the CSS (after changing `src/theme/input.css`):

```bash
cd src/theme && npm install && npm run build:css
```

### Environment variables

| Variable | Description |
|---|---|
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | PostgreSQL connection credentials |
| `POSTGRES_HOST` / `POSTGRES_PORT` | Database address and port |
| `DJANGO_SECRET_KEY` | Django secret key (the dev default is for development only) |
| `DJANGO_DEBUG` | `true` for development only; defaults to `False` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated list of allowed hosts (also the basis for `CSRF_TRUSTED_ORIGINS`) |
| `DJANGO_ADMIN_PATH` | Admin panel path, defaults to `admin/` |

## Tests and lint

```bash
ruff check src
ruff format --check src
PYTHONPATH=src pytest
```

The tests cover the key scenarios: account creation, invitation link protection, joining, suggestion permissions, agreement replacement, suggestion ties, and finalized event restrictions.

## Project structure

```
src/
├── config/        # Django settings and root URLs
├── accounts/      # Custom User, signup / login / logout
├── events/        # Event, Participation, Suggestion, Agreement models
│                  #   + coordination services and Jalali date templatetags
├── templates/     # Persian/RTL templates
├── static/        # CSS, JS, fonts and vendor libraries
└── manage.py
specs/             # Feature specifications and plans (spec-driven)
```

## Workflow

1. The host signs up and creates an event.
2. They send the invitation link to the guests.
3. Guests log in and open the link to join the event.
4. Each participant submits their own date suggestions and agrees on other people's suggestions.
5. Once at least one non-host agreement has been made, the host finalizes the event and the chosen suggestion is recorded as the final one.
