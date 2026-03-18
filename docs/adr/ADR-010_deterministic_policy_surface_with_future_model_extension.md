# ADR-010: Deterministic Policy Surface with Future Model Extension

Status: Accepted

## Context

The v1 recommendation engine should remain deterministic and explainable. At the same time, the architecture should not lock the product into a rule-only future if later experimentation justifies model-assisted ranking.

A direct embedding of rule logic into runtime code would make future transition difficult. Conversely, introducing a model too early would reduce explainability and destabilize the system before the learner-state and guardrail surfaces are mature.

## Decision

The project will:
- use a deterministic recommendation policy in v1;
- preserve a stable policy surface for future model-assisted extension;
- keep candidate generation and hard guardrails deterministic even if scoring later becomes model-assisted.

The stable surface includes:
- `RecommendationContext`
- bounded `CandidateAction[]`
- `RecommendationDecision`
- decision logging requirements

## Consequences

### Positive
- v1 remains debuggable and explainable
- future model-assisted ranking can be introduced without rewriting the surrounding system
- safety / anti-loop constraints remain stable
- offline evaluation becomes easier because context and decision contracts are preserved

### Trade-offs
- initial design must be more deliberate about interfaces and logging
- deterministic v1 policy may underperform a future learned ranker in edge cases
- future model integration still requires evaluation discipline, not just plugging in a scorer

## Rejected alternatives

### Alternative A — embed rule logic directly inside runtime orchestration
Rejected because it destroys policy modularity and future extensibility.

### Alternative B — introduce a learned recommendation model in v1
Rejected because the surrounding evidence, guardrail, and state surfaces are not yet mature enough to support it safely.
