import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { LauncherShell, type LauncherShellProps } from "./LauncherShell";

function buildProps(
  overrides: Partial<LauncherShellProps> = {},
): LauncherShellProps {
  return {
    restoreError: "",
    recommendation: {
      decision_id: "rec.1000",
      policy_version: "bootstrap.recommendation.v1",
      decision_mode: "rule_based",
      candidate_actions: [],
      chosen_action: {
        mode: "MockInterview",
        session_intent: "ReadinessCheck",
        target_type: "scenario",
        target_id: "scenario.rate-limiter.basic",
        difficulty_profile: "standard",
        strictness_profile: "strict",
        session_size: "single_unit",
        delivery_profile: "text_first",
        rationale: "Validate rate-limiter readiness through one bounded mock pass.",
      },
      supporting_signals: ["mock_readiness_available"],
      blocking_signals: [],
      rationale: "Validate rate-limiter readiness through one bounded mock pass.",
      alternatives_summary: "Study and practice remain available as lower-pressure fallbacks.",
    },
    recommendationError: "",
    isLoadingRecommendation: false,
    learnerSummary: {
      user_id: "demo-user",
      readiness_summary: {
        category: "moderate",
        title: "Moderate readiness",
        detail: "Mock interview is available but a few weak areas remain.",
      },
      weak_areas: [
        {
          target_kind: "concept",
          target_id: "concept.rate-limiter.failure-handling",
          title: "Failure handling",
          summary: "Degraded behavior is still weakly evidenced.",
        },
      ],
      review_due: [
        {
          target_kind: "concept",
          target_id: "concept.rate-limiter.algorithm-choice",
          title: "Algorithm choice",
          summary: "Revisit token bucket trade-offs soon.",
        },
      ],
      evidence_posture: {
        category: "mixed",
        title: "Evidence is converging",
        details: ["Reviewed practice and mock evidence are both present."],
      },
    },
    summaryError: "",
    isLoadingSummary: false,
    launchOptions: [
      {
        unit_id: "elu.scenario_readiness_check.mock_interview.readiness_check.scenario.rate-limiter.basic",
        content_id: "scenario.rate-limiter.basic",
        topic_slug: "rate-limiter",
        display_title: "Design a Rate Limiter",
        visible_prompt:
          "Design a Rate Limiter for a multi-tenant API where strict fairness matters more than occasional burst throughput.",
        effective_difficulty: "standard",
      },
      {
        unit_id:
          "elu.scenario_readiness_check.mock_interview.readiness_check.scenario.rate-limiter.fairness",
        content_id: "scenario.rate-limiter.fairness",
        topic_slug: "rate-limiter",
        display_title: "Design a Strict Fairness Limiter",
        visible_prompt:
          "Design a Rate Limiter where tenant fairness matters more than peak burst absorption.",
        effective_difficulty: "standard",
      },
    ],
    launcherError: "",
    isLoadingOptions: false,
    selectedUnitId:
      "elu.scenario_readiness_check.mock_interview.readiness_check.scenario.rate-limiter.basic",
    sessionError: "",
    isStartingSession: false,
    onStartRecommendedSession: vi.fn(),
    onSelectUnit: vi.fn(),
    onStartSession: vi.fn(),
    onRetryRestore: vi.fn(),
    onDiscardSavedSession: vi.fn(),
    ...overrides,
  };
}

describe("LauncherShell", () => {
  it("renders recommendation, learner summary, and launch options without family-specific assumptions", () => {
    const props = buildProps();

    render(<LauncherShell {...props} />);

    expect(screen.getByText("Deterministic recommendation")).toBeInTheDocument();
    expect(
      screen.getByText("Validate rate-limiter readiness through one bounded mock pass."),
    ).toBeInTheDocument();
    expect(screen.getByText("Current evidence snapshot")).toBeInTheDocument();
    expect(screen.getByText("Failure handling")).toBeInTheDocument();
    expect(screen.getByText("Backend-provided manual options")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Design a Rate Limiter for a multi-tenant API where strict fairness matters more than occasional burst throughput.",
      ),
    ).toBeInTheDocument();
  });

  it("forwards launcher actions through callbacks", () => {
    const onStartRecommendedSession = vi.fn();
    const onSelectUnit = vi.fn();
    const onStartSession = vi.fn();
    const props = buildProps({
      onStartRecommendedSession,
      onSelectUnit,
      onStartSession,
    });

    render(<LauncherShell {...props} />);

    fireEvent.click(screen.getByRole("button", { name: "Start recommended session" }));
    fireEvent.click(screen.getByRole("radio", { name: /Strict Fairness Limiter/i }));
    fireEvent.click(screen.getByRole("button", { name: "Start session" }));

    expect(onStartRecommendedSession).toHaveBeenCalledTimes(1);
    expect(onSelectUnit).toHaveBeenCalledWith(
      "elu.scenario_readiness_check.mock_interview.readiness_check.scenario.rate-limiter.fairness",
    );
    expect(onStartSession).toHaveBeenCalledTimes(1);
  });

  it("renders the restore recovery branch when a saved session cannot be restored", () => {
    const onRetryRestore = vi.fn();
    const onDiscardSavedSession = vi.fn();
    const props = buildProps({
      restoreError: "Saved session could not be restored.",
      onRetryRestore,
      onDiscardSavedSession,
    });

    render(<LauncherShell {...props} />);

    expect(screen.getByText("Saved session could not be restored.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Retry saved session" }));
    fireEvent.click(screen.getByRole("button", { name: "Discard saved session" }));

    expect(onRetryRestore).toHaveBeenCalledTimes(1);
    expect(onDiscardSavedSession).toHaveBeenCalledTimes(1);
    expect(screen.queryByText("Deterministic recommendation")).not.toBeInTheDocument();
  });
});
