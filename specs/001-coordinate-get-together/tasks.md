---
description: "Task list for Coordinate Get-Together implementation"
---

# Tasks: Coordinate Get-Together

**Input**: Design documents from `/specs/001-coordinate-get-together/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md, constitution.md

**Tests**: REQUIRED. Constitution Principle III ("Quality Is Verified") requires automated tests for every behavior change, including intended behavior and relevant failure or boundary cases. The plan's constitution check requires automated tests for the acceptance scenarios and permission boundaries. Write each story's tests first and confirm they fail before implementing that story.

**Organization**: Tasks are grouped by user story so each story can be implemented, tested, and delivered independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- Server-rendered Django application under `src/`
- Project config: `src/config/`
- Apps: `src/accounts/`, `src/events/`
- Templates: `src/templates/`
## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the repository layout and toolchain described in plan.md

- [ ] T001 Create the source layout from plan.md: `src/manage.py`, `src/config/` (`settings.py`, `urls.py`, `wsgi.py`, `__init__.py`), `src/accounts/` (`models.py`, `forms.py`, `views.py`, `apps.py`, `__init__.py`, `tests/`), `src/events/` (`models.py`, `forms.py`, `views.py`, `apps.py`, `__init__.py`, `tests/`), `src/templates/` (`base.html`, `accounts/`, `events/`), `src/theme/` (`input.css`, `package.json`), and `src/static/css/`
- [ ] T002 Pin Python dependencies in `requirements.txt` to Django 6.1.2, psycopg, pytest, pytest-django, and Ruff, matching research.md
- [ ] T003 [P] Configure Ruff lint and format checks for `src/` in `pyproject.toml` so `ruff check src` and `ruff format --check src` match quickstart.md
- [ ] T004 [P] Configure pytest-django in `pyproject.toml` (`DJANGO_SETTINGS_MODULE` for `config.settings`, `pythonpath = ["src"]`) so `PYTHONPATH=src pytest` matches quickstart.md
- [ ] T005 [P] Add Tailwind CSS v4 CLI to `src/theme/package.json` and write `src/theme/input.css` that scans `src/templates/` and compiles to `src/static/css/app.css`
- [ ] T006 [P] Document required environment variable names with no secret values in `.env.example`, including `DATABASE_URL`, and add `.env.dev` to `.gitignore`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 Configure `src/config/settings.py` for Python 3.12 and Django 6.1.2: read `DATABASE_URL` from the process environment (local development exports `.env.dev`), set PostgreSQL via psycopg, enable sessions and CSRF, set `AUTH_USER_MODEL` to the custom email user, and configure template and static directories at `src/templates/` and `src/static/`
- [ ] T008 Implement the custom user model in `src/accounts/models.py` based on `AbstractUser` with `USERNAME_FIELD = "email"`, `email` required, unique, and case-insensitive, `password` stored only as a Django password hash, `name` required and 1–150 characters after trimming whitespace, and `is_active` so inactive users cannot authenticate. Use `name` as the display-name field noted in data-model.md (the design's `display_name` should be named `name`).
- [ ] T009 Create and apply the initial accounts migration for the custom user in `src/accounts/migrations/`
- [ ] T010 [P] Create the shared page shell in `src/templates/base.html` that loads `src/static/css/app.css`, includes the CSRF token on POST forms, and shows sign-in and sign-up links for anonymous visitors and a logout action for authenticated users
- [ ] T011 [P] Register app routes in `src/config/urls.py` so later stories can attach `/`, `/accounts/signup/`, `/accounts/login/`, `/accounts/logout/`, `/events/new/`, and `/events/<token>/` without changing the project URL layout again
- [ ] T012 Compile Tailwind from `src/theme/input.css` to the committed stylesheet `src/static/css/app.css` with `@tailwindcss/cli` so the app can run without Node.js after the CSS is built

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 - Create and Share a Get-Together (Priority: P1) 🎯 MVP

**Goal**: A signed-in organizer creates a get-together with a required title and optional details, is identified as its organizer, and can copy a unique opaque invitation link.

**Independent Test**: A registered user can create an event, obtain its unique link, and open the event as its organizer. A blank title creates no event.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T013 [P] [US1] Add model tests in `src/events/tests/test_models.py` for Event: `title` required and 1–200 characters after trimming whitespace, `details` optional and maximum 5,000 characters, `invite_token` required, unique, and unguessable, `status` enum `active` or `finalized` with new events starting as `active`, `organizer` required and immutable after creation, and `final_suggestion` null while active
- [ ] T014 [P] [US1] Add model tests in `src/events/tests/test_participation.py` for Participation: one participation per user and event, organizer participation created with the event, and `joined_at` set when the participation is created
- [ ] T015 [P] [US1] Add integration tests in `src/events/tests/test_create_event.py` for the US1 acceptance scenarios: a signed-in user who submits a title creates an event with themselves as organizer and participant; the organizer can retrieve a unique invitation URL at `/events/<invite_token>/`; a missing or whitespace-only title shows a field-specific error and creates no event

### Implementation for User Story 1

- [ ] T016 [P] [US1] Implement the Event model in `src/events/models.py` with `organizer` (foreign key to User, required, immutable after creation), `title` (required, 1–200 characters after trimming whitespace), `details` (optional, maximum 5,000 characters), `invite_token` (required, unique, unguessable, generated by the server with Django's cryptographically secure token generation), `status` (`active` or `finalized`; new events start as `active`), `final_suggestion` (null while active), and `created_at`
- [ ] T017 [P] [US1] Implement the Participation model in `src/events/models.py` with `event` and `user` required, `joined_at` set on creation, and a uniqueness constraint of one participation per user and event
- [ ] T018 [US1] Create the events migration in `src/events/migrations/` for Event and Participation, including database uniqueness of one invitation token per event and one participation per user and event
- [ ] T019 [US1] Implement the event create form in `src/events/forms.py`: `title` required, 1–200 characters after trimming whitespace, empty results rejected with a field-specific message; `details` optional, at most 5,000 characters
- [ ] T020 [US1] Implement `GET/POST /events/new/` in `src/events/views.py`: authenticated only; on success assign the signed-in user as organizer, generate `invite_token`, create the organizer's participation, set status `active`, and redirect to the event page
- [ ] T021 [US1] Implement the participant event page `GET /events/<token>/` for the organizer in `src/events/views.py` and `src/templates/events/detail.html`, showing title, details, organizer, status, the organizer's display name, and the absolute invitation URL for copying
- [ ] T022 [US1] Add the create-event template `src/templates/events/new.html` and a signed-in home listing of the user's events at `GET /` in `src/templates/home.html` and `src/events/views.py`
- [ ] T023 [US1] Wire `/events/new/` and `/events/<token>/` in `src/events/urls.py` and include them from `src/config/urls.py`

**Checkpoint**: User Story 1 is independently functional. An organizer can create a titled event and copy its opaque invitation link.

## Phase 4: User Story 2 - Join an Event Through Its Link (Priority: P1)

**Goal**: An unauthenticated visitor who opens a valid event link must sign up or sign in before seeing event content, then returns to that event as a participant. Invalid links show a generic unavailable message.

**Independent Test**: An unauthenticated visitor follows a valid event link, registers an account, and is returned to the intended event as a participant. An invalid token shows an unavailable-event page with no event content.

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T024 [P] [US2] Add account form and model tests in `src/accounts/tests/test_signup.py`: `email` required, valid, and unique without regard to case; `password` required and validated by Django's password validators and stored only as a hash; `name` required, 1–150 characters after trimming whitespace; a duplicate email is rejected with a message directing the person to sign in and creates no user
- [ ] T025 [P] [US2] Add authentication view tests in `src/accounts/tests/test_auth.py`: sign-up creates an active user and signs them in; sign-in starts a session for a valid email and password; unknown email, wrong password, and inactive account all return the same generic failure message; logout ends the session; sign-in and sign-up honor a safe internal `next` URL and reject an external `next`
- [ ] T026 [P] [US2] Add invitation access tests in `src/events/tests/test_join.py`: an anonymous `GET /events/<token>/` redirects to sign-in and preserves the event URL; completing sign-up or sign-in from that URL returns the visitor to the event as a participant; a signed-in person opening a valid active event link joins and can view it; an invalid token shows a generic unavailable-event page with no title, details, participants, suggestions, or final decision

### Implementation for User Story 2

- [ ] T027 [P] [US2] Implement the sign-up form in `src/accounts/forms.py` with `email` (required, valid, unique without regard to case), `password` (required, Django password validators), and `name` (required after whitespace trimming, 1–150 characters). An existing email redisplays the form and tells the person to sign in.
- [ ] T028 [P] [US2] Implement the sign-in form in `src/accounts/forms.py` with `email` and `password`. Unknown email, wrong password, and inactive account must produce the same generic failure message.
- [ ] T029 [US2] Implement `GET/POST /accounts/signup/` and `GET/POST /accounts/login/` in `src/accounts/views.py`: create an active user and sign them in, start a session for valid credentials, and honor a safe internal `next` URL so an invitation destination survives authentication
- [ ] T030 [US2] Implement `POST /accounts/logout/` in `src/accounts/views.py` so an authenticated caller ends the session, and register `/accounts/signup/`, `/accounts/login/`, and `/accounts/logout/` in `src/accounts/urls.py`
- [ ] T031 [US2] Add templates `src/templates/accounts/signup.html` and `src/templates/accounts/login.html` that never render the password back, and update `GET /` in `src/templates/home.html` to show sign-in and sign-up entry points for anonymous visitors
- [ ] T032 [US2] Update `GET /events/<token>/` in `src/events/views.py` so an anonymous visitor is redirected to sign-in with this URL preserved, a signed-in user joins only while the event is `active`, and an unknown token renders the generic unavailable page
- [ ] T033 [US2] Add `src/templates/events/unavailable.html` with a clear unavailable-event message and no event title, details, participants, suggestions, or final decision
- [ ] T034 [US2] Show every participant's `name` on the event page in `src/templates/events/detail.html` so a second participant who joined through the link is visible

**Checkpoint**: User Stories 1 and 2 both work. An invitee can register from a link and land on that event without reopening it.

## Phase 5: User Story 3 - Make and Agree to Suggestions (Priority: P2)

**Goal**: A participant adds a time-and-place suggestion and participants record one movable agreement per event, with every action attributed to the responsible person. Authors edit or delete their own suggestions; the organizer may delete any suggestion but may edit only suggestions they authored.

**Independent Test**: Two registered participants can add suggestions and record agreement; the event shows the author and agreeing participants for each suggestion. Agreeing to a second suggestion moves the agreement. Non-authors cannot edit or delete a suggestion, except the organizer may delete it.

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T035 [P] [US3] Add Suggestion model tests in `src/events/tests/test_suggestions.py`: `event` required and immutable; `author` is a foreign key to Participation, required and immutable, and `author.event` must equal `event`; `proposed_at` is a required timezone-aware datetime; `location` is required and 1–200 characters after trimming whitespace; `description` is optional and 1–2,000 characters after trimming whitespace; empty location or missing datetime is rejected and creates no suggestion; no rule requires `proposed_at` to be in the future
- [ ] T036 [P] [US3] Add Agreement model tests in `src/events/tests/test_agreements.py`: one agreement per participation and event; `participant.event`, `event`, and `suggestion.event` must all match; agreeing to another suggestion updates that row instead of creating a second agreement; creating or editing a suggestion does not create, delete, or move any agreement; deleting a suggestion deletes its agreements; replacement stays in one row under concurrent requests
- [ ] T037 [P] [US3] Add suggestion and agreement view tests in `src/events/tests/test_suggestion_views.py` covering the HTTP contract: `POST /events/<token>/suggestions/` creates a suggestion attributed to the caller's participation; `POST .../edit/` is allowed only for the author while active; `POST .../delete/` is allowed for the author or the organizer while active; `POST .../agree/` moves the participant's one agreement; anonymous callers redirect to sign-in; authenticated non-participants and callers without the required role receive HTTP 403; a suggestion that does not belong to the event in the URL receives HTTP 404; a missing datetime or blank location redisplays the form and creates no suggestion

### Implementation for User Story 3

- [ ] T038 [P] [US3] Implement the Suggestion model in `src/events/models.py` with `event` (required, immutable), `author` (foreign key to Participation, required, immutable; `author.event` must equal `event`), `proposed_at` (required timezone-aware `DateTimeField`), `location` (required, 1–200 characters after trimming whitespace), `description` (optional, 1–2,000 characters after trimming whitespace), `created_at`, and `updated_at` updated when `proposed_at` or `location` changes. Enforce `suggestion.author.event == suggestion.event`.
- [ ] T039 [P] [US3] Implement the Agreement model in `src/events/models.py` with `event` (required, immutable), `suggestion` (required; its event must equal `event`), `participant` (foreign key to Participation, required, immutable; the participation's event must equal `event`), `created_at`, and `updated_at` updated when the agreement moves. Enforce uniqueness of one agreement per participation and event, and `agreement.participant.event == agreement.event == agreement.suggestion.event`.
- [ ] T040 [US3] Add the Suggestion and Agreement migration in `src/events/migrations/`, including the same-event constraints and the one-agreement-per-participation-and-event uniqueness constraint. Wire `Event.final_suggestion` to Suggestion in this migration.
- [ ] T041 [US3] Implement the suggestion form in `src/events/forms.py`: `proposed_at` required as one datetime value; `location` required, 1–200 characters after trimming whitespace; `description` optional, 1–2,000 characters after trimming whitespace. Trim location before validation and reject an empty result with a field-specific message. A blank location or missing date and time must not create a suggestion.
- [ ] T042 [US3] Implement suggestion create, edit, and delete in `src/events/views.py`: only while the event is `active`; assign `author` to the signed-in user's participation; the author may edit or delete; the organizer may delete any suggestion but may edit a suggestion only when the organizer's participation is its `author`; deleting a suggestion deletes its agreements; editing `proposed_at` or `location` does not clear or move existing agreements; a non-participant receives HTTP 403; a suggestion that does not belong to the token's event receives HTTP 404
- [ ] T043 [US3] Implement `POST /events/<token>/suggestions/<id>/agree/` in `src/events/views.py` inside a transaction: a participant has at most one agreement per event; agreeing to another suggestion updates that row's suggestion and `updated_at` rather than creating a second agreement; the displayed identity is the participation's user
- [ ] T044 [US3] Update `src/templates/events/detail.html` to list every suggestion's date and time, location, description when present, author name, and the display names of agreeing participants, and to show create, edit, delete, and agree actions only when the current user is allowed to perform them
- [ ] T045 [US3] Register suggestion and agreement routes in `src/events/urls.py`: `POST /events/<token>/suggestions/`, `POST /events/<token>/suggestions/<id>/edit/`, `POST /events/<token>/suggestions/<id>/delete/`, and `POST /events/<token>/suggestions/<id>/agree/`

**Checkpoint**: User Stories 1–3 work independently. Participants can propose a time and place, attribute it, and move a single agreement.

## Phase 6: User Story 4 - View Participants and Finalize an Event (Priority: P2)

**Goal**: Participants can see who belongs to the event. Only the organizer can finalize, and only after at least one agreement by someone other than the organizer. The highest-count suggestion is final; a tie requires the organizer to choose exactly one. Finalization locks changes and hides the event from non-participants.

**Independent Test**: Participants can view the participant list. An organizer can finalize the unique highest-agreement suggestion, or must choose one tied suggestion. Finalization is refused when no non-organizer agreement exists. Non-participants cannot access a finalized event, and participants cannot change suggestions or agreements after finalization.

### Tests for User Story 4 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T046 [P] [US4] Add finalization service tests in `src/events/tests/test_finalize.py`: only the organizer can finalize an `active` event; the event must have at least one agreement made by someone other than the organizer, and the organizer's own agreement does not count; the selected suggestion must belong to the event and its agreement count must equal the highest count; a unique highest suggestion may be submitted directly; a tie requires exactly one of the tied suggestions; finalization locks the event row, recounts agreements, and rejects a selection that is no longer among the highest-count suggestions; success sets `status` to `finalized` and stores `final_suggestion`; the transition is irreversible
- [ ] T047 [P] [US4] Add finalized-event view tests in `src/events/tests/test_finalized_access.py`: participants see title, details, participant identities, and the final suggestion but cannot create, edit, delete, or agree; unauthenticated visitors and authenticated non-participants receive the same generic unavailable page with no event content and the invitation link adds no participation; suggestion and agreement posts on a finalized event return HTTP 403 and do not change stored data; a non-organizer `POST /events/<token>/finalize/` returns HTTP 403; a missing or ineligible selection redisplays the tie choices with an error

### Implementation for User Story 4

- [ ] T048 [US4] Implement finalization in `src/events/views.py` for `POST /events/<token>/finalize/`: accept `suggestion_id` only when the caller is the organizer, the event is `active`, the suggestion belongs to the event, at least one agreement was made by someone other than the organizer (the organizer's own agreement does not count), and the suggestion's agreement count equals the highest count. Lock the event row, recount agreements inside a transaction, set `status` to `finalized`, and store `final_suggestion`.
- [ ] T049 [US4] Show tied suggestions in `src/events/views.py` and `src/templates/events/detail.html`: when several suggestions share the highest agreement count, offer only those suggestions and require exactly one selection; a missing or ineligible selection redisplays those choices with an error; a unique highest suggestion may be submitted directly
- [ ] T050 [US4] Enforce the finalized lock in `src/events/views.py`: after `status` is `finalized`, reject suggestion creation, editing, deletion, and agreement changes with HTTP 403 and do not change stored data; a final suggestion cannot be deleted
- [ ] T051 [US4] Hide finalized events from non-participants in `src/events/views.py`: an unknown token and an authenticated non-participant opening a finalized event both render the generic unavailable page with no event content, and the invitation link creates no new participation after finalization. Existing participants retain read access.
- [ ] T052 [US4] Update `src/templates/events/detail.html` so every participant sees all participant identities and, when finalized, the final suggestion, while create, edit, delete, agree, and finalize actions are omitted unless the current user is allowed to perform them
- [ ] T053 [US4] Register `POST /events/<token>/finalize/` in `src/events/urls.py`

**Checkpoint**: All four user stories are independently functional. An organizer can close an event on the winning suggestion, and the outcome stays private to participants.

---

---
## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Quality gates and cross-cutting checks that span the stories

- [ ] T054 [P] Recompile and commit `src/static/css/app.css` from `src/theme/input.css` so templates for accounts, events, suggestions, and finalization are styled without a Node.js runtime
- [ ] T055 [P] Confirm `.env.example` lists every variable read by `src/config/settings.py` without secret values, and that local `DATABASE_URL` stays only in untracked `.env.dev`
- [ ] T056 Review authorization and validation messages in `src/accounts/views.py`, `src/events/views.py`, and the templates so duplicate accounts, invalid links, and authorization failures stay field-specific or generic and never reveal event title, details, participants, suggestions, or the final decision
- [ ] T057 Run the quickstart.md validation commands from the repository root with `.env.dev` exported: `ruff check src`, `ruff format --check src`, and `PYTHONPATH=src pytest`. The suite must cover account creation, protected invitation access, participation, suggestion permissions, agreement replacement, tie handling, and finalized-event restrictions.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US1 and US2 are both P1. Implement US1 first because US2 joins an event US1 creates. After the US1 models exist, US2 account tests and forms can proceed in parallel with US1 views.
  - US3 (P2) depends on US1 Event and Participation and on US2 authenticated participants
  - US4 (P2) depends on US3 suggestions and agreements, because finalization counts those agreements
- **Polish (Phase 7)**: Depends on the user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — no dependency on other stories
- **User Story 2 (P1)**: Can start after Foundational for account pages. Joining an event integrates with US1's event page and should be tested with an event created by US1.
- **User Story 3 (P2)**: Depends on US1 models and US2 participation. Independently testable with two signed-in participants.
- **User Story 4 (P2)**: Depends on US3 agreement rows. Independently testable by finalizing an event that already has suggestions and a non-organizer agreement.

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before migrations, forms, and views
- Services and permission checks before templates
- Story complete before moving to the next priority

### Parallel Opportunities

## Parallel Example: User Story 1

```bash
# Write the failing US1 tests together:
Task: "Add Event model tests in src/events/tests/test_models.py"
Task: "Add Participation model tests in src/events/tests/test_participation.py"
Task: "Add create-event integration tests in src/events/tests/test_create_event.py"

# Then implement the two US1 models together:
Task: "Implement Event in src/events/models.py"
Task: "Implement Participation in src/events/models.py"
```

## Parallel Example: User Story 2

```bash
Task: "Add signup tests in src/accounts/tests/test_signup.py"
Task: "Add auth view tests in src/accounts/tests/test_auth.py"
Task: "Add invitation join tests in src/events/tests/test_join.py"

Task: "Implement signup form in src/accounts/forms.py"
Task: "Implement sign-in form in src/accounts/forms.py"
```

## Parallel Example: User Story 3

```bash
Task: "Add Suggestion model tests in src/events/tests/test_suggestions.py"
Task: "Add Agreement model tests in src/events/tests/test_agreements.py"
Task: "Add suggestion view tests in src/events/tests/test_suggestion_views.py"

Task: "Implement Suggestion in src/events/models.py"
Task: "Implement Agreement in src/events/models.py"
```

## Parallel Example: User Story 4

```bash
Task: "Add finalization service tests in src/events/tests/test_finalize.py"
Task: "Add finalized-access view tests in src/events/tests/test_finalized_access.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: A signed-in user can create a titled event and copy its opaque invitation link; a blank title is rejected
5. Demo the organizer flow before building accounts-from-a-link

### Incremental Delivery

1. Setup + Foundational → project runs, custom email user exists
2. User Story 1 → organizers can create and share an event (MVP)
3. User Story 2 → invitees can sign up from a link and join before finalization
4. User Story 3 → participants propose a time and place and move one agreement
5. User Story 4 → organizer finalizes the winning suggestion and the event locks
6. Polish → Ruff, pytest, and the committed stylesheet match quickstart.md

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. After Foundational:
   - Developer A: User Story 1 event models, form, and page
   - Developer B: User Story 2 account forms and auth pages
3. After US1 and US2:
   - Developer A: User Story 3 suggestions and agreements
   - Developer B: prepare US4 tests against the agreement rules
4. Developer A or B finishes User Story 4 only after agreement rows exist

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps a task to a specific user story for traceability
- Tests are required by the constitution, not optional for this feature
- The interface field is `name` (1–150 characters after trimming), not `display_name`, per the data-model note
- Suggestion `description` is optional (1–2,000 characters after trimming). The HTTP contract's required fields remain `proposed_at` and `location`.
- Do not add password recovery, external identity providers, invitation expiry, participant removal, comments, ranking, live updates, caching, or a way to reopen a finalized event
- Commit after each task or logical group
- Stop at any checkpoint to validate that story independently

- T003, T004, T005, and T006 can run in parallel after T001
- T010 and T011 can run in parallel after T007 and T008
- US1 tests T013, T014, and T015 can run in parallel; models T016 and T017 can run in parallel
- US2 tests T024, T025, and T026 can run in parallel; forms T027 and T028 can run in parallel
- US3 tests T035, T036, and T037 can run in parallel; models T038 and T039 can run in parallel
- US4 tests T046 and T047 can run in parallel
- Polish tasks T054 and T055 can run in parallel

---


---

---


## Phase 8: Convergence

**Purpose**: Close the gap between the artifacts and the current implementation (convergence run 2026-10-25). Findings and priorities were reviewed with the product owner before execution.

- [x] T058 Repair the five template tags split across newlines in `src/templates/events/detail.html` so every event-detail render succeeds per FR-005…FR-022 (partial)
- [x] T059 Show every participant's name on the event page in `src/templates/events/detail.html` per FR-016 (missing)
- [x] T060 Prefill each suggestion's edit form in `src/templates/events/detail.html` with that suggestion's current values per US3/AC4 and FR-017 (partial)
- [x] T061 Translate `src/templates/home.html`, `src/templates/events/unavailable.html`, and all user-facing validation messages in `src/accounts/forms.py`, `src/events/forms.py`, `src/events/models.py`, and `src/events/services.py` into natural Persian per user direction and SC-001/SC-003 (partial)
- [x] T062 Redesign `src/templates/home.html` and `src/templates/events/unavailable.html` with the existing design system, add the missing `.error` style to `src/theme/input.css`, and recompile `src/static/css/app.css` per user direction (partial)
- [x] T063 Set `LANGUAGE_CODE="fa"` and `TIME_ZONE="Asia/Tehran"` in `src/config/settings.py` and verify Jalali input, stored instants, and displayed Tehran times with regression tests per user direction (partial)
- [x] T064 Document the `django-jalali` dependency rationale in `requirements.txt` per Constitution I (unrequested)
- [x] T065 Consolidate the duplicated invitation-join tests into `src/events/tests/test_join.py` and remove `src/events/tests/test_join_event.py` per Constitution II (unrequested)
