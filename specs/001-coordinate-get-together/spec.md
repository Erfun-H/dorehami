# Feature Specification: Coordinate Get-Together

**Feature Branch**: `main`

**Created**: 2026-10-21

**Status**: Draft

**Input**: User description: "Coordinate get-togethers through user accounts, shared event links, attributable suggestions, and agreements."

## Clarifications

### Session 2026-10-23

- Q: After an event is finalized, should a signed-in person who opens its valid invitation link become a participant, or should the link no longer grant access? → A: The link no longer grants access or adds participants after finalization.
- Q: What should happen if the organizer finalizes an event when none of its suggestions has an agreement made by someone other than the organizer? → A: Do not allow finalization until at least one agreement has been made by someone other than the organizer. The organizer's own agreement does not count toward this requirement.
- Q: Once an event is finalized, should participants still be able to create, edit, delete, or change agreements on suggestions? → A: No; finalization locks all suggestion and agreement changes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create and Share a Get-Together (Priority: P1)

A signed-in organizer creates a get-together with a title and optional details, then copies a unique event link to invite friends.

**Why this priority**: Creating and sharing an event establishes the collaboration space and is necessary before friends can participate.

**Independent Test**: A registered user can create an event, obtain its unique link, and open the event as its organizer.

**Acceptance Scenarios**:

1. **Given** a signed-in user, **When** they provide a title and create a get-together, **Then** the event is saved with them identified as its organizer.
2. **Given** an existing get-together, **When** its organizer requests the invitation link, **Then** they receive a unique link that opens that event.
3. **Given** an organizer creates an event without a title, **When** they submit it, **Then** they are told that a title is required and no event is created.

---

### User Story 2 - Join an Event Through Its Link (Priority: P1)

A friend who receives an event link signs up or signs in before viewing and participating in the event, so every contribution has an identifiable author.

**Why this priority**: Required identity is essential to attribute suggestions and agreements to the correct participant.

**Independent Test**: An unauthenticated visitor follows a valid event link, registers an account, and is returned to the intended event as a participant.

**Acceptance Scenarios**:

1. **Given** an unauthenticated visitor opens a valid event link, **When** they try to access the event, **Then** they are prompted to sign up or sign in before event content is shown.
2. **Given** a visitor completes sign-up from a valid event link, **When** registration succeeds, **Then** they are signed in and taken to that event as a participant.
3. **Given** a signed-in person opens a valid event link, **When** the event loads, **Then** they can view it as a participant.
4. **Given** a person opens an invalid or unavailable event link, **When** it is resolved, **Then** they see a clear unavailable-event message without access to event content.

---

### User Story 3 - Make and Agree to Suggestions (Priority: P2)

A participant adds a suggestion for the get-together and participants can record agreement with it, with each action visibly attributed to the responsible person.

**Why this priority**: Suggestions and agreements turn an invitation into a useful coordination tool while preserving clear accountability.

**Independent Test**: Two registered participants can add suggestions and record their agreement; the event shows the author and agreeing participants for each suggestion.

**Acceptance Scenarios**:

1. **Given** a signed-in event participant, **When** they submit a non-empty suggestion, **Then** the event displays the suggestion with them identified as its author.
2. **Given** a suggestion in an event, **When** another signed-in participant agrees to it, **Then** the suggestion displays that participant's agreement.
3. **Given** a participant who agrees to one suggestion, **When** they agree to a different suggestion in the same event, **Then** their agreement is moved to the latter suggestion and no longer counts for the former suggestion.
4. **Given** a participant-created suggestion, **When** its author edits or deletes it, **Then** the change is applied; no other participant may edit or delete it, except that the organizer may delete it.
5. **Given** a visitor who is not signed in, **When** they attempt to add or agree to a suggestion through an event link, **Then** they must sign up or sign in before the action can be completed.

---

### User Story 4 - View Participants and Finalize an Event (Priority: P2)

Participants can view the people who belong to their event. The organizer finalizes the event using the most-agreed suggestion, resolving a tie by selecting one tied suggestion; the finalized event and decision remain visible only to its participants.

**Why this priority**: Participants need visibility into the group, and a final decision completes the coordination process while protecting the event's private outcome.

**Independent Test**: Participants can view an event's participant list; an organizer can finalize an event with a highest-agreement suggestion or choose one tied highest-agreement suggestion; non-participants cannot access the finalized event.

**Acceptance Scenarios**:

1. **Given** an event participant, **When** they view the event, **Then** they can view the identities of all participants belonging to that event.
2. **Given** an event with one suggestion having more agreements than every other suggestion, **When** its organizer finalizes the event, **Then** that suggestion is recorded and displayed as the final suggestion.
3. **Given** an event with multiple suggestions tied for the highest agreement count, **When** its organizer finalizes the event, **Then** the system displays all and only the tied suggestions and requires the organizer to select exactly one as final.
4. **Given** an event whose only agreements, if any, were made by its organizer, **When** its organizer attempts to finalize it, **Then** finalization is refused with a clear message.
5. **Given** a finalized event, **When** an unauthenticated visitor or an authenticated non-participant accesses its event details or invitation link, **Then** no event details or final suggestion are displayed and the link does not add them as a participant.
6. **Given** a finalized event, **When** a participant views it, **Then** they can view its event details and final suggestion but cannot create, edit, delete, or agree to suggestions.

### Edge Cases

- Altered, deleted, or otherwise unavailable event links must not reveal event details.
- An email address already associated with an account must direct the person to sign in rather than create a duplicate account.
- Empty or whitespace-only event titles and suggestions must be rejected with an understandable message.
- Returning to an event link after sign-in must direct the person to that event rather than a generic landing page.
- Agreement state must remain associated with the participant who made it when multiple people use the same event.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow a person to create an account using an email address and password.
- **FR-002**: The system MUST allow a registered user to sign in and sign out.
- **FR-003**: The system MUST require authentication before a person can view an event reached through an invitation link.
- **FR-004**: The system MUST preserve the destination event while an unauthenticated visitor completes sign-up or sign-in from its invitation link.
- **FR-005**: The system MUST allow a signed-in user to create a get-together with a required title and optional descriptive details.
- **FR-006**: The system MUST identify the user who creates an event as that event's organizer.
- **FR-007**: The system MUST generate a unique invitation link for each event and allow its organizer to retrieve that link for sharing.
- **FR-008**: The system MUST allow a signed-in person who opens a valid invitation link to participate in the linked event before it is finalized; after finalization, the link MUST neither grant access nor add participants.
- **FR-009**: The system MUST prevent event details from being displayed for invalid or unavailable invitation links and show a clear message instead.
- **FR-010**: The system MUST allow an authenticated event participant to create a non-empty suggestion within an event that is not finalized.
- **FR-011**: The system MUST display each suggestion with the identity of the participant who created it.
- **FR-012**: The system MUST allow an authenticated event participant to record agreement with a suggestion in an event that is not finalized.
- **FR-013**: The system MUST display the identities of participants who have agreed with each suggestion.
- **FR-014**: The system MUST maintain at most one active agreement per participant per event; agreeing to a different suggestion in that event MUST replace the participant's previous agreement.
- **FR-015**: The system MUST prevent unauthenticated visitors from creating suggestions or recording agreements.
- **FR-016**: The system MUST allow every event participant to view the identities of all participants belonging to that event.
- **FR-017**: The system MUST allow a participant to edit or delete only suggestions they created; it MUST prohibit them from editing or deleting suggestions created by other participants.
- **FR-018**: The system MUST allow an event organizer to delete any suggestion in their event but MUST allow them to edit another participant's suggestion only when they are also that suggestion's original author.
- **FR-019**: The system MUST enforce suggestion editing and deletion permissions for every request, independent of whether the user interface displays an action.
- **FR-020**: The system MUST allow only the organizer to finalize an event that has at least one agreement made by someone other than the organizer. The organizer's own agreement MUST NOT count toward this requirement.
- **FR-021**: When finalizing an event, the system MUST record and display the suggestion with the highest agreement count as the final suggestion; when multiple suggestions are tied for the highest count, it MUST display those tied suggestions to the organizer and require selection of exactly one final suggestion.
- **FR-022**: The system MUST prevent unauthenticated visitors and authenticated non-participants from viewing a finalized event's details or final suggestion, including through its invitation link; only existing participants may view them.
- **FR-023**: After an event is finalized, the system MUST prevent all suggestion creation, editing, deletion, and agreement changes.

### Key Entities

- **User**: A registered person with account credentials and an identifiable name or email address; may organize events or participate in them.
- **Event**: A get-together created by a user, with a title, optional details, one organizer, one unique invitation link, a status of active or finalized, and one final suggestion when finalized.
- **Participation**: A user's authenticated association with an event after accessing its valid invitation link before the event is finalized.
- **Suggestion**: A proposed detail or idea for an event, created by one participant and associated with that event; it may be selected as the event's final suggestion.
- **Agreement**: A participant's recorded support for one suggestion; uniquely associated with one participant and one event, and assigned to only one suggestion in that event at a time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 90% of new users can create an account and sign in on their first attempt in under 2 minutes.
- **SC-002**: At least 90% of organizers can create a titled event and copy its invitation link in under 1 minute.
- **SC-003**: At least 90% of invited visitors who complete registration reach the intended event without needing to reopen the link.
- **SC-004**: In usability testing, at least 90% of participants can add a suggestion and record agreement with another suggestion in under 1 minute.
- **SC-005**: For 100 simultaneous active participants across shared events, at least 95% of event views and submitted suggestions become visible to the participant within 2 seconds.
- **SC-006**: In a review of event activity, 100% of displayed suggestions and agreements identify the authenticated participant responsible for the action.

## Assumptions

- The first release uses email address and password credentials; external identity providers and password recovery are outside this feature's scope.
- Any signed-in person with a valid event invitation link may participate in that event before it is finalized; invitation expiration, approval workflows, and participant removal are outside this feature's scope.
- An event's title is sufficient for its initial creation; date, time, location, and other planning fields are optional descriptive details.
- Participants can create, edit, and delete suggestions and record one changeable agreement per event until the event is finalized; ranking, commenting, reopening a finalized event, and changing its final suggestion are outside this feature's scope.
- Event links are intended to be shared by the organizer with trusted friends; the application clearly identifies users but does not provide additional invitation verification in this release.
- Account and event information is retained while the account and event remain active, subject to the application's standard privacy and account-management policies.
