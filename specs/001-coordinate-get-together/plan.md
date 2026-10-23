# Implementation Plan: Coordinate Get-Together

**Branch**: `001-coordinate-get-together` | **Date**: 2026-10-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-coordinate-get-together/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Signed-in people can create a get-together, share an opaque invitation link, join before finalization, propose suggestions, and record one movable agreement per event. The organizer finalizes the highest-agreed suggestion only after at least one agreement has been made by someone other than the organizer; the organizer's own agreement does not count. The organizer chooses one suggestion when there is a tie. Finalization locks changes and hides the event from everyone who is not already a participant.

The application is one server-rendered Django 6.1 project backed by PostgreSQL 16. Django forms, sessions, and transactions enforce validation and permissions. Tailwind CSS v4 styles the templates through a compiled static stylesheet, with no frontend framework.

## Technical Context

**Language/Version**: Python 3.12.3

**Primary Dependencies**: Django 6.1.2, psycopg, Tailwind CSS v4 CLI, pytest, pytest-django, Ruff

**Storage**: PostgreSQL 16

**Testing**: pytest with pytest-django; Django test client for page and permission flows

**Target Platform**: Linux server, developed and validated locally

**Project Type**: Server-rendered web application

**Performance Goals**: For 100 simultaneous active participants, at least 95% of event views and submitted suggestions become visible within 2 seconds

**Constraints**: Email and password authentication only; no password recovery, external identity providers, invitation expiry, participant removal, comments, or reopening a finalized event; server-side authorization on every request; invitation links must not reveal unavailable events

**Scale/Scope**: Small private events among friends; five persisted entities; account, event, suggestion, agreement, and finalization flows

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Simplicity**: Pass. One Django project uses the framework's templates, forms, authentication, and ORM. No API, frontend framework, cache, or task queue is introduced.
- **Readability**: Pass. Accounts, events, and coordination are separate Django apps with focused models, forms, and views. Shared rules live in the model and transaction layer rather than being copied into templates.
- **Verified quality**: Pass. The implementation phase must include automated tests for the acceptance scenarios and permission boundaries, plus Ruff linting and formatting. The quickstart names the required commands.
- **Maintainable boundaries**: Pass. The HTTP contract, data model, and quickstart document the externally visible behavior. Out-of-scope account recovery and invitation management are not given unused extension points.
- **Sustainable ownership**: Pass. Each app owns its models and tests. The compiled CSS is a generated artifact with a documented source file and build command.
- **Dependencies**: Pass. Django, its PostgreSQL driver, Tailwind, pytest, and Ruff each serve a stated requirement. No dependency is added for authentication or styling beyond those requirements.
- **Error handling and configuration**: Pass. Duplicate accounts, invalid links, and authorization failures have generic or field-specific messages that do not expose private event data. Database credentials come from environment variables. Local development reads them from `.env.dev`; `.env.example` only documents the variable names.

No constitutional violation requires justification.

## Project Structure

### Documentation (this feature)

```text
specs/001-coordinate-get-together/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
.env.example
.env.dev
requirements.txt
src/
├── manage.py
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   └── tests/
├── events/
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   └── tests/
├── templates/
│   ├── base.html
│   ├── accounts/
│   └── events/
├── theme/
│   ├── input.css
│   └── package.json
└── static/
    └── css/
        └── app.css
```

**Structure Decision**: Keep non-code project files at the repository root and place the application under `src/`. The root holds `requirements.txt`, `.env.example`, and `.env.dev`. `.env.example` is the committed list of required variables and contains no secrets. `.env.dev` is the local development file; create it from the example, put the local `DATABASE_URL` there, and do not commit credentials. Django reads configuration from the process environment, so development commands export `.env.dev` before starting the app or tests. `src/` contains `manage.py`, the `config` project, and the `accounts` and `events` apps. Accounts own the custom email user and authentication pages. Events own participations, suggestions, agreements, and finalization. Server-rendered templates live in `src/templates/`, Tailwind source lives in `src/theme/`, and compiled CSS lives in `src/static/css/`. This keeps source code in one directory without splitting the interface from the server that authorizes it.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations.

## Post-Design Constitution Check

- The data model uses five entities already required by the specification. Participation and Agreement are explicit because their uniqueness rules cannot be represented safely as informal lists.
- The HTTP contract uses Django form posts rather than a parallel API.
- Finalization and agreement replacement require transactions, which is the smallest mechanism that preserves their concurrency rules.
- Tailwind compilation is confined to one stylesheet build and does not add a client-side application.

The post-design check passes without exceptions.
