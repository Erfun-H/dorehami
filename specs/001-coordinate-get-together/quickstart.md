# Quickstart: Coordinate Get-Together

This guide validates the planned application after implementation. It does not contain implementation code. Field names and routes are defined in [data-model.md](data-model.md) and [contracts/http-interface.md](contracts/http-interface.md).

## Prerequisites

- Python 3.12.
- PostgreSQL 16 running locally.
- Node.js and npm available when rebuilding Tailwind CSS.
- A virtual environment created from the repository root.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
createdb dorehami
cp .env.example .env.dev
```

Set `DATABASE_URL` in `.env.dev` to the local PostgreSQL database. Export that file, then initialize and start the application from the repository root:

```bash
set -a
source .env.dev
set +a
python src/manage.py migrate
python src/manage.py runserver
```

The application is then available at `http://127.0.0.1:8000/`.

## Automated validation

From the activated virtual environment, with `.env.dev` exported:

```bash
set -a
source .env.dev
set +a
ruff check src
ruff format --check src
PYTHONPATH=src pytest
```

Expected result: Ruff reports no issues and the test suite passes. The tests must cover account creation, protected invitation access, participation, suggestion permissions, agreement replacement, tie handling, and finalized-event restrictions.

## Manual end-to-end scenarios

### Create and share an event

1. Open the application and create an account with an email, password, and display name.
2. Create an event with a title and optional details.
3. Confirm the event page identifies the creator as organizer and participant.
4. Copy the invitation link and confirm it contains an opaque token rather than a sequential id.
5. Submit an event with a blank title and confirm no event is created.

### Join through the link

1. Open the invitation link in a private browser session.
2. Confirm event details are not visible before authentication.
3. Create a second account and confirm the browser returns to the same event.
4. Confirm both display names appear in the participant list.
5. Open an altered token and confirm the page says the event is unavailable without showing event content.
6. Try the first email address again and confirm the page directs the visitor to sign in.

### Suggest and agree

1. As the second participant, add a suggestion with both a date and time and a location, and confirm its author is shown.
2. As the organizer, add another suggestion and agree to the first one.
3. Agree to the second suggestion and confirm the agreement moved rather than appearing on both.
4. Confirm the second participant cannot edit or delete the organizer's suggestion.
5. Confirm the organizer can delete another participant's suggestion.
6. Submit a suggestion without a date and time or without a location and confirm it is rejected.

### Finalize and lock

1. Attempt to finalize an event when the only agreement, if any, was made by the organizer and confirm it is refused.
2. Add two suggestions, give them equal agreements, and confirm finalization requires one of the tied choices.
3. Finalize one tied suggestion and confirm participants can see it as final.
4. Confirm suggestion creation, editing, deletion, and agreement changes are rejected.
5. Open the original link as a third signed-in user and confirm no details are shown and no participant is added.
6. Open the same link without signing in and confirm it neither reveals content nor joins the event after authentication.
