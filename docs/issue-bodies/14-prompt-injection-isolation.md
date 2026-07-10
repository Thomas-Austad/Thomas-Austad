## Context and motivation
Job descriptions, ATS payloads, resumes, LinkedIn exports, and user-provided text are currently passed into model prompts as plain interpolated content. These sources are untrusted and may contain prompt-injection instructions that try to alter tool use, policy, approval state, or data disclosure.

## Acceptance criteria
- Untrusted content is clearly delimited and labeled before being sent to any model.
- System/developer policy, typed application state, and approval records cannot be overridden by retrieved or uploaded text.
- Model outputs are validated for policy-sensitive invariants after schema parsing.
- Prompt-injection attempts in job descriptions and candidate documents are detected, ignored, or safely surfaced without changing permissions or approvals.

## Relevant files or components
- `app/agents/profile_agent.py`
- `app/agents/match_agent.py`
- `app/agents/application_agent.py`
- `app/agents/compensation_agent.py`
- `app/services/openai_service.py`
- connector and resume-ingestion paths that feed model prompts

## Dependencies or blockers
- Should be coordinated with the profile review, application approval, and auth/audit issues.
- No external provider changes are required.

## Security considerations
- This is a release-blocking trust boundary for a product that consumes third-party job content and user documents.
- Retrieved text must never choose tools, destinations, credentials, permissions, approval state, or externally consequential actions.
- Avoid placing unrelated private context into prompts when only a subset of data is needed.

## Testing considerations
- Add negative tests with prompt-injection strings in job descriptions, resumes, and screening questions.
- Assert that injected instructions do not change application status, generated approvals, tool choice, or disclosed data.
- Prefer invariant checks over brittle assertions on model prose.
