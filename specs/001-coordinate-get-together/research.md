# Research: Coordinate Get-Together

## Decision: Server-rendered Django application

- **Decision**: Implement one Django project that renders HTML templates. Use Django views and forms for every user action; do not add a separate API service or frontend framework.
- **Rationale**: The feature is a small authenticated web application: account creation, event pages, suggestions, agreements, and finalization. Django already provides routing, forms, validation, sessions, CSRF protection, and the ORM. A separate frontend would add a second application without serving a current requirement.
- **Alternatives considered**: A Django REST API plus a React or Vue client was rejected because it duplicates validation and authorization and adds a runtime the feature does not need. A static frontend calling the database directly was rejected because authorization must be enforced on the server.

## Decision: Django 6.1.2 on Python 3.12

- **Decision**: Use Django 6.1.2, the current stable release, with the repository's Python 3.12.3 interpreter.
- **Rationale**: Django 6.1 supports Python 3.12, 3.13, 3.14, and 3.15. Python 3.12 is already installed, so no runtime upgrade is required. The project is new, so there is no compatibility reason to start on an older Django release.
- **Alternatives considered**: Django 5.2 LTS was considered for a longer support window. It was rejected for a new application because 6.1 is the current stable release and supports the installed Python version. Django 6.0 was rejected because 6.1 is the newer compatible stable series.

## Decision: PostgreSQL 16 with psycopg

- **Decision**: Use PostgreSQL 16, which is already installed, through Django's PostgreSQL backend and the current `psycopg` driver. Configure the connection with environment variables. Local development stores them in `.env.dev` at the repository root and keeps credentials out of source control. `.env.example` documents the same variable names without secret values.
- **Rationale**: PostgreSQL provides the unique constraints and transactions needed for one invitation token per event, one participation per user and event, and one agreement per user and event. The installed server is version 16, so no database upgrade is needed.
- **Alternatives considered**: SQLite was rejected because PostgreSQL is an explicit project requirement. A hosted database or connection pooler was rejected because neither is required for local development or the stated scale.
## Decision: Built-in authentication with a custom email user

- **Decision**: Use Django's authentication, sessions, password hashing, login, and logout. Start with a custom user model based on `AbstractUser`, set email as the unique identifier, and use `USERNAME_FIELD = "email"`. Do not add social login or password recovery.
- **Rationale**: Django recommends choosing a custom user model at the start of a project because replacing the user model later is difficult. Email-and-password accounts are the specified credential model. Built-in password hashing and session authentication satisfy sign-up, sign-in, and sign-out without another dependency.
- **Alternatives considered**: The default username-based `User` model was rejected because accounts are identified by email. Third-party authentication packages were rejected because they add maintenance and features that are outside this release.

## Decision: Tailwind CSS v4 compiled with its CLI

- **Decision**: Style server-rendered templates with Tailwind CSS v4 utility classes. Compile `src/theme/input.css` to `src/static/css/app.css` with `@tailwindcss/cli`. Commit the compiled stylesheet so the application can run without Node.js after the CSS has been built.
- **Rationale**: Tailwind is an explicit styling requirement. The CLI scans templates and emits static CSS with no browser runtime and no JavaScript UI framework. Committing the output keeps the Python application independently runnable.
- **Alternatives considered**: The Tailwind CDN was rejected because production styling should not depend on a remote script. A PostCSS or Vite pipeline was rejected because there is no JavaScript application to bundle. Hand-written CSS was rejected because it does not meet the Tailwind requirement.

## Decision: Django templates, forms, and transactions

- **Decision**: Use Django templates for pages, Django forms for input validation, and database transactions with row locks for agreement changes and finalization. Enforce object permissions in the view layer for every request.
- **Rationale**: Templates and forms are the smallest implementation of the specified pages. Transactions make replacing an agreement and selecting one final suggestion atomic. Server-side permission checks satisfy the requirement that hidden interface actions cannot bypass authorization.
- **Alternatives considered**: Client-side-only validation was rejected because empty titles, permissions, and finalization rules must hold on every request. An asynchronous task queue was rejected because all actions complete within one request.

## Decision: Opaque invitation tokens

- **Decision**: Store a unique, unguessable token on each event and expose it in `/events/<token>/`. Use Django's cryptographically secure token generation. Return the same generic unavailable response for unknown tokens and for authenticated non-participants after finalization.
- **Rationale**: The invitation link must identify one event before finalization and must not reveal details when it is invalid or no longer grants access. An opaque token avoids exposing sequential database IDs.
- **Alternatives considered**: Sequential numeric IDs were rejected because they are easy to guess and can reveal whether events exist. Signed expiring links were rejected because invitation expiration is outside this release.

## Decision: Test and quality tooling

- **Decision**: Use Django's test framework with pytest and pytest-django. Cover models, forms, and view authorization with unit and integration tests. Format and lint Python with Ruff. Do not add a type checker until the project adopts static typing.
- **Rationale**: pytest-django runs the same Django tests while providing concise fixtures. Ruff replaces separate formatting and linting tools with one maintained dependency. The constitution requires automated tests and passing formatter and linter checks.
- **Alternatives considered**: Unittest alone was rejected because pytest fixtures make multi-user event scenarios easier to read. Black plus Flake8 was rejected as two tools where one suffices. A browser-automation suite was rejected for the initial gate; the Django test client covers the server behavior, and the quickstart documents the manual usability checks.

## Performance and scope

- **Decision**: Target the stated load of 100 simultaneous participants with ordinary indexed relational queries. Do not add caching, background jobs, or pagination in the first implementation.
- **Rationale**: Event pages read one event, its participants, suggestions, and agreements. Indexes on the foreign keys and unique constraints are sufficient for the stated two-second visibility target. Adding cache infrastructure before a measurement would violate the constitution.
- **Alternatives considered**: Redis caching and websocket updates were rejected because the feature does not require live updates or a measured bottleneck.

## Decision: Structured time-and-place suggestions

- **Decision**: Replace the free-text suggestion body with a required timezone-aware `proposed_at` `DateTimeField` and a required `location` string. Reference the author and agreeing participant through `Participation`, constrained to the suggestion's event.
- **Rationale**: The group is choosing one time and place. Both parts are necessary for a selectable option, while a description, duration, or map point is not. Participation is the event membership, so it can enforce same-event authorship; the displayed identity remains the participation's user.
- **Alternatives considered**: A free-text body was rejected because it does not identify the chosen time and place. Separate date and time fields were rejected because the requested representation is one datetime. A direct user foreign key was rejected because it cannot enforce membership in the suggestion's event. Optional location was rejected because a time without a place is not a complete option. Automatically clearing existing agreements was rejected: a new suggestion getting lost among other messages is a visibility problem, not an invalidation of previous agreements. Agreements change only when a participant agrees to a different suggestion, or when their suggestion is deleted.

