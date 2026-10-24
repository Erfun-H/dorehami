# Tasks: Get-Together Event Coordination

**Input**: Design documents from `/specs/001-get-together-events/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included. The specification requires acceptance scenarios and the plan mandates test-driven development.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Every task includes the exact file path where the work happens

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize the Django project and shared tooling

- [X] T001 Create the Django project configuration, app packages, and server entry point in `src/config/`, `src/accounts/`, `src/events/`, and `src/manage.py`
- [X] T002 Add pinned Django, PostgreSQL, environment, and test dependencies to `requirements.txt` and `requirements-dev.txt`
- [X] T003 [P] Configure Ruff, pytest, and Django settings for local development in `pyproject.toml` and `src/config/settings.py`
- [X] T004 [P] Add the Tailwind CSS v4 build configuration and compiled stylesheet in `src/theme/package.json`, `src/theme/input.css`, and `src/static/css/app.css`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core account and application infrastructure that blocks every user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create the custom email-based user model and manager in `src/accounts/models.py` and generate its initial migration
- [X] T006 [P] Implement account signup, login, and logout forms and views in `src/accounts/forms.py` and `src/accounts/views.py`
- [X] T007 [P] Create the responsive base template and account templates in `src/templates/base.html`, `src/templates/accounts/signup.html`, and `src/templates/accounts/login.html`
- [X] T008 Register account and event routes and the home view in `src/config/urls.py` and `src/events/views.py`
- [X] T009 Add shared pytest fixtures and database setup for authenticated users in `src/conftest.py`

**Checkpoint**: Accounts and application infrastructure are ready for story implementation

---

## Phase 3: User Story 1 - Create an Event (Priority: P1) 🎯 MVP

**Goal**: A signed-in user creates a get-together and receives an unguessable invitation link

**Independent Test**: Sign in, submit an event title, and verify the resulting event page shows the organizer and invitation URL

### Tests for User Story 1

- [X] T010 [P] [US1] Write failing account tests for email-only signup, case-insensitive duplicate rejection, login, and logout in `src/accounts/tests/test_accounts.py`
- [X] T011 [P] [US1] Write failing model tests for an event with a trimmed title of at most 200 characters, optional details of at most 5,000 characters, an unguessable unique invitation token of at least 32 characters, an immutable required organizer, and an initial active status with no final suggestion in `src/events/tests/test_models.py`
- [X] T012 [P] [US1] Write a failing test that creating an event creates exactly one organizer participation and rejects a second participation for the same user in `src/events/tests/test_participation.py`
- [X] T013 [P] [US1] Write a failing integration test that a signed-in user can submit a title and optional details, is redirected to the invitation URL, and receives a field error for a blank title in `src/events/tests/test_create_event.py`

### Implementation for User Story 1

- [X] T014 [US1] Implement `Event` and `Participation` models, constraints, and invitation-token generation in `src/events/models.py`, then generate their initial migration
- [X] T015 [US1] Implement the event creation form and signed-in creation/detail views in `src/events/forms.py` and `src/events/views.py`, including the invitation URL and organizer participation
- [X] T016 [US1] Make event creation and detail templates usable on a phone in `src/templates/events/new.html` and `src/templates/events/detail.html`

**Checkpoint**: User Story 1 is independently functional and testable
