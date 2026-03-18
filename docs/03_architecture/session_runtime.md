# Session Runtime

## Purpose
Session Runtime owns how one bounded learning session unfolds. It does not own long-term learner state.

## Top-level modes
Only three top-level runtime modes exist in v1:
- `Study`
- `Practice`
- `MockInterview`

A mode is justified only if it changes session goal, expected answer shape, help policy, follow-up behavior, scoring posture, and evidence meaning.

## Session intent
`SessionIntent` is a separate axis that explains why a session is being run:
- `LearnNew`
- `Reinforce`
- `Remediate`
- `SpacedReview`
- `ReadinessCheck`

Intent modifies content selection, strictness, and recommendation interpretation. It is not a top-level mode.

## Mode summaries
### Study
- concept-focused retrieval and explanation
- hints commonly allowed
- reveal may be allowed
- lighter evaluation

### Practice
- applied reasoning in bounded drills or mini-scenarios
- moderate follow-up envelope
- stricter evaluation than Study

### MockInterview
- readiness-oriented design conversation
- constrained help policy
- stronger follow-up pressure
- full review expected

## Review in runtime
`Review` is not a top-level mode. In runtime it appears as:
- `ReviewReport` after evaluation
- `ReviewQueue` as later planning input
- remediation or spaced review as session intents

## Runtime responsibilities
- resolve the next bounded learning unit from the chosen action
- emit semantic events for meaningful boundaries
- preserve transcript and timing summaries
- hand off stable answer boundaries to evaluation
- attach evaluation results and expose the resulting review artifact
- close sessions deterministically as completed or abandoned

## See also
For executable transition semantics, use `docs/03_architecture/session_runtime_state_machine_v1.md`.
