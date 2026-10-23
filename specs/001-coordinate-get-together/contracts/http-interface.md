# HTTP Interface: Coordinate Get-Together

This is a server-rendered HTML interface. All state-changing requests use `POST` and Django CSRF protection. Successful form submissions redirect to the relevant page. Field errors are redisplayed with the submitted form.

Authentication uses a session cookie. Unauthenticated requests to protected pages redirect to sign-in and preserve the requested URL. Passwords appear only in request bodies and are never rendered back to the page.

## Pages

| Method | Path | Caller | Result |
|---|---|---|---|
| GET | `/` | Any visitor | Shows sign-in and sign-up entry points, or the signed-in user's events |
| GET | `/accounts/signup/` | Anonymous | Shows the account form |
| POST | `/accounts/signup/` | Anonymous | Creates an active user and signs them in |
| GET | `/accounts/login/` | Anonymous | Shows the sign-in form |
| POST | `/accounts/login/` | Anonymous | Starts a session for valid email and password |
| POST | `/accounts/logout/` | Authenticated | Ends the session |
| GET | `/events/new/` | Authenticated | Shows the event form |
| POST | `/events/new/` | Authenticated | Creates an active event and organizer participation |
| GET | `/events/<token>/` | Anonymous | Redirects to sign-in with this URL preserved |
| GET | `/events/<token>/` | Authenticated participant, or any authenticated user while active | Shows the event and joins if it is still active |
| GET | `/events/<token>/` | Unknown token, or non-participant after finalization | Shows a generic unavailable-event page |
| POST | `/events/<token>/suggestions/` | Participant while active | Creates a suggestion |
| POST | `/events/<token>/suggestions/<id>/edit/` | Author while active | Updates that suggestion |
| POST | `/events/<token>/suggestions/<id>/delete/` | Author or organizer while active | Deletes that suggestion and its agreements |
| POST | `/events/<token>/suggestions/<id>/agree/` | Participant while active | Moves that participant's one agreement to this suggestion |
| POST | `/events/<token>/finalize/` | Organizer while active | Finalizes the event with the selected eligible suggestion |

## Account contract

Sign-up fields:

- `email`: required, valid, unique without regard to case.
- `password`: required and validated by Django's password validators.
- `display_name`: required after whitespace trimming.

An existing email redisplays the form and tells the person to sign in. No duplicate user is created.

Sign-in fields are `email` and `password`. Unknown email, wrong password, and inactive account all return the same generic failure message. Sign-in and sign-up honor a safe internal `next` URL, which is how an invitation destination survives authentication.

## Event contract

Create fields:

- `title`: required, 1–200 characters after trimming.
- `details`: optional, at most 5,000 characters.

The server assigns the signed-in user as organizer, generates `invite_token`, creates the organizer's participation, and redirects to the event page. The page shows the absolute invitation URL for copying.

The event page for a participant shows:

- title, details, organizer, and status;
- every participant's display name;
- every suggestion's date and time, location, author, and the display names of agreeing participants;
- the final suggestion when the status is `finalized`;
- actions only when the current user is allowed to perform them.

The unavailable page contains no event title, details, participants, suggestions, or final decision.

## Suggestion and agreement contract

Suggestion fields are:

- `proposed_at`: required date and time, submitted as one datetime value.
- `location`: required, 1–200 characters after trimming.

A missing datetime or blank location redisplays the form and creates no suggestion. The server assigns the suggestion's author to the signed-in user's participation in that event. A signed-in user who does not participate receives HTTP 403.

Authorization responses:

- Anonymous callers are redirected to sign-in.
- Authenticated callers who are not participants, or who do not have the required role, receive HTTP 403.
- Changes to a finalized event receive HTTP 403 and do not change stored data.
- A suggestion that does not belong to the event in the URL receives HTTP 404.

Agreement creation or movement returns the participant to the event page. The previous suggestion no longer lists that participant, and the selected suggestion does.

## Finalization contract

The organizer submits `suggestion_id`.

The server accepts the request only when all of these are true:

- the caller is the organizer;
- the event is active;
- the suggestion belongs to the event;
- the event has at least one agreement made by someone other than the organizer; the organizer's own agreement does not count;
- the suggestion's agreement count equals the highest count in the event.

A unique highest suggestion may be submitted directly. When several suggestions share that count, the page offers only those suggestions and requires one selection. A missing or ineligible selection redisplays the tie choices with an error. Any other caller receives HTTP 403.

On success, the event status becomes `finalized`, `final_suggestion` is stored, and subsequent suggestion or agreement posts are rejected. Participants can still view the event and its final suggestion.
