import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

const fetchMock = vi.fn();
const SESSION_RESUME_STORAGE_KEY = "sysdrill.activeSession.v1";
const RECOMMENDATION_STORAGE_KEY = "sysdrill.launcherRecommendation.v1";

describe("App", () => {
  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
    window.localStorage.clear();
  });

  it("loads a recommendation and reaches review through the recommendation-driven flow", async () => {
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse({
          decision_id: "rec.0001",
          policy_version: "bootstrap.recommendation.v1",
          decision_mode: "rule_based",
          candidate_actions: [
            {
              mode: "Study",
              session_intent: "LearnNew",
              target_type: "concept",
              target_id: "concept.alpha-topic",
              difficulty_profile: "introductory",
              strictness_profile: "supportive",
              session_size: "single_unit",
              delivery_profile: "text_first",
            },
          ],
          chosen_action: {
            mode: "Study",
            session_intent: "LearnNew",
            target_type: "concept",
            target_id: "concept.alpha-topic",
            difficulty_profile: "introductory",
            strictness_profile: "supportive",
            session_size: "single_unit",
            delivery_profile: "text_first",
            rationale:
              "Start with a supportive Study / LearnNew unit on 'Кэширование' because there is no reviewed evidence for this concept yet.",
          },
          supporting_signals: [
            "no_prior_reviewed_attempt_for_target",
            "bootstrap_exploration_bias",
          ],
          blocking_signals: [],
          rationale:
            "Start with a supportive Study / LearnNew unit on 'Кэширование' because there is no reviewed evidence for this concept yet.",
          alternatives_summary:
            "Practice actions remain available but are downranked until there is reviewed evidence for this concept.",
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          mode: "Study",
          session_intent: "LearnNew",
          items: [
            {
              unit_id: "elu.concept_recall.study.learn_new.concept.alpha-topic",
              content_id: "concept.alpha-topic",
              topic_slug: "alpha-topic",
              display_title: "Кэширование",
              visible_prompt: "Explain caching.",
              effective_difficulty: "introductory",
            },
          ],
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          session_id: "session.0001",
          state: "awaiting_answer",
          recommendation_decision_id: "rec.0001",
          current_unit: {
            id: "elu.concept_recall.study.learn_new.concept.alpha-topic",
            visible_prompt: "Explain caching.",
          },
        }),
      )
      .mockResolvedValueOnce(jsonResponse({ state: "evaluation_pending" }))
      .mockResolvedValueOnce(
        jsonResponse({
          session_id: "session.0001",
          state: "review_presented",
          evaluation_result: {
            evaluation_id: "evaluation.0001",
            weighted_score: 0.67,
            overall_confidence: 0.74,
            missing_dimensions: ["trade_off_articulation"],
          },
          review_report: {
            strengths: ["The answer explains the concept itself in working terms."],
            missed_dimensions: ["Trade-off articulation"],
            reasoning_gaps: ["Trade-offs stay shallow."],
            recommended_next_focus: "Add the main trade-offs next time.",
            support_dependence_note: null,
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          decision_id: "rec.0002",
          policy_version: "bootstrap.recommendation.v1",
          decision_mode: "rule_based",
          candidate_actions: [
            {
              mode: "Study",
              session_intent: "SpacedReview",
              target_type: "concept",
              target_id: "concept.alpha-topic",
              difficulty_profile: "standard",
              strictness_profile: "supportive",
              session_size: "single_unit",
              delivery_profile: "text_first",
            },
          ],
          chosen_action: {
            mode: "Study",
            session_intent: "SpacedReview",
            target_type: "concept",
            target_id: "concept.alpha-topic",
            difficulty_profile: "standard",
            strictness_profile: "supportive",
            session_size: "single_unit",
            delivery_profile: "text_first",
            rationale:
              "Review the same concept again because the last reviewed session completed successfully.",
          },
          supporting_signals: ["recommendation_completed"],
          blocking_signals: [],
          rationale:
            "Review the same concept again because the last reviewed session completed successfully.",
          alternatives_summary:
            "Reinforcement and remediation actions remain available if the next reviewed outcome weakens.",
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          mode: "Study",
          session_intent: "SpacedReview",
          items: [
            {
              unit_id: "elu.concept_recall.study.spaced_review.concept.alpha-topic",
              content_id: "concept.alpha-topic",
              topic_slug: "alpha-topic",
              display_title: "Кэширование",
              visible_prompt: "Explain caching again with the main trade-offs.",
              effective_difficulty: "standard",
            },
          ],
        }),
      );

    render(<App />);

    expect(
      await screen.findByText(
        "Start with a supportive Study / LearnNew unit on 'Кэширование' because there is no reviewed evidence for this concept yet.",
      ),
    ).toBeInTheDocument();
    expect(await screen.findByText("Кэширование")).toBeInTheDocument();
    const practiceRemediateRadio = screen.getByRole("radio", {
      name: /Practice \/ Remediate/i,
    });
    expect(practiceRemediateRadio).toBeEnabled();
    expect(screen.getByText("bootstrap.recommendation.v1")).toBeInTheDocument();

    await waitFor(() => {
      expect(
        screen.getByRole("button", {
          name: "Start recommended session",
        }),
      ).toBeEnabled();
    });

    fireEvent.click(screen.getByRole("button", { name: "Start recommended session" }));

    expect(
      await screen.findByRole("textbox", {
        name: "Your answer",
      }),
    ).toBeInTheDocument();
    expect(practiceRemediateRadio).toBeDisabled();
    expect(screen.getByRole("heading", { name: "Study / Learn New" })).toBeInTheDocument();

    fireEvent.change(screen.getByRole("textbox", { name: "Your answer" }), {
      target: {
        value: "Caching stores frequently used data to reduce latency and backend load.",
      },
    });

    fireEvent.click(screen.getByRole("button", { name: "Request review" }));

    expect(await screen.findByText("Weighted score")).toBeInTheDocument();
    expect(screen.getByText("0.67")).toBeInTheDocument();
    expect(screen.getByText("Add the main trade-offs next time.")).toBeInTheDocument();
    expect(practiceRemediateRadio).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Back to launcher" }));

    expect(await screen.findByText("Backend-provided manual options")).toBeInTheDocument();
    expect(practiceRemediateRadio).toBeEnabled();

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(7);
    });
    expect(fetchMock.mock.calls[0]?.[0]).toContain("/recommendations/next");
    expect(fetchMock.mock.calls[1]?.[0]).toContain("/runtime/manual-launch-options");
    expect(fetchMock.mock.calls[2]?.[0]).toContain(
      "/runtime/sessions/start-from-recommendation",
    );
    expect(fetchMock.mock.calls[5]?.[0]).toContain("/recommendations/next");
    expect(fetchMock.mock.calls[6]?.[0]).toContain("/runtime/manual-launch-options");
  });

  it("shows recommendation errors explicitly while leaving manual fallback visible", async () => {
    fetchMock
      .mockResolvedValueOnce(errorResponse(503, "runtime content is not configured"))
      .mockResolvedValueOnce(
        jsonResponse({
          mode: "Study",
          session_intent: "LearnNew",
          items: [
            {
              unit_id: "elu.concept_recall.study.learn_new.concept.alpha-topic",
              content_id: "concept.alpha-topic",
              topic_slug: "alpha-topic",
              display_title: "Кэширование",
              visible_prompt: "Explain caching.",
              effective_difficulty: "introductory",
            },
          ],
        }),
      );

    render(<App />);

    expect(
      await screen.findByText("runtime content is not configured"),
    ).toBeInTheDocument();
    expect(await screen.findByText("Backend-provided manual options")).toBeInTheDocument();
  });

  it("retries review without resubmitting the answer after evaluate fails", async () => {
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse({
          decision_id: "rec.0001",
          policy_version: "bootstrap.recommendation.v1",
          decision_mode: "rule_based",
          candidate_actions: [],
          chosen_action: {
            mode: "Study",
            session_intent: "LearnNew",
            target_type: "concept",
            target_id: "concept.alpha-topic",
            difficulty_profile: "introductory",
            strictness_profile: "supportive",
            session_size: "single_unit",
            delivery_profile: "text_first",
            rationale: "Start here.",
          },
          supporting_signals: [],
          blocking_signals: [],
          rationale: "Start here.",
          alternatives_summary: "",
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          mode: "Study",
          session_intent: "LearnNew",
          items: [
            {
              unit_id: "elu.concept_recall.study.learn_new.concept.alpha-topic",
              content_id: "concept.alpha-topic",
              topic_slug: "alpha-topic",
              display_title: "Кэширование",
              visible_prompt: "Explain caching.",
              effective_difficulty: "introductory",
            },
          ],
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          session_id: "session.0001",
          state: "awaiting_answer",
          current_unit: {
            id: "elu.concept_recall.study.learn_new.concept.alpha-topic",
            visible_prompt: "Explain caching.",
          },
        }),
      )
      .mockResolvedValueOnce(jsonResponse({ state: "evaluation_pending" }))
      .mockResolvedValueOnce(errorResponse(503, "temporary evaluate failure"))
      .mockResolvedValueOnce(errorResponse(409, "review is not available when session state is 'evaluation_pending'"))
      .mockResolvedValueOnce(
        errorResponse(409, "cannot attach evaluation when session state is 'review_presented'"),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          session_id: "session.0001",
          state: "review_presented",
          evaluation_result: {
            evaluation_id: "evaluation.0001",
            weighted_score: 0.67,
            overall_confidence: 0.74,
            missing_dimensions: ["trade_off_articulation"],
          },
          review_report: {
            strengths: ["The answer explains the concept itself in working terms."],
            missed_dimensions: ["Trade-off articulation"],
            reasoning_gaps: ["Trade-offs stay shallow."],
            recommended_next_focus: "Add the main trade-offs next time.",
            support_dependence_note: null,
          },
        }),
      );

    render(<App />);

    await screen.findByText("Start here.");
    await waitFor(() => {
      expect(
        screen.getByRole("button", {
          name: "Start recommended session",
        }),
      ).toBeEnabled();
    });

    fireEvent.click(screen.getByRole("button", { name: "Start recommended session" }));
    fireEvent.change(await screen.findByRole("textbox", { name: "Your answer" }), {
      target: {
        value: "Caching stores frequently used data to reduce latency and backend load.",
      },
    });

    fireEvent.click(screen.getByRole("button", { name: "Request review" }));
    expect(await screen.findByText("temporary evaluate failure")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Request review" }));

    expect(await screen.findByText("Weighted score")).toBeInTheDocument();
    expect(screen.getByText("0.67")).toBeInTheDocument();

    const calls = fetchMock.mock.calls.map((call) => String(call[0]));
    expect(
      calls.filter((url) => url.includes("/runtime/sessions/session.0001/answer")),
    ).toHaveLength(1);
    expect(
      calls.filter((url) => url.includes("/runtime/sessions/session.0001/evaluate")),
    ).toHaveLength(2);
    expect(
      calls.filter((url) => url.includes("/runtime/sessions/session.0001/review")),
    ).toHaveLength(2);
  });

  it("restores an awaiting-answer session from local storage", async () => {
    setStoredSessionEnvelope({
      sessionId: "session.0042",
      transcript: "Draft answer kept in the browser.",
      answerSubmitted: false,
    });
    fetchMock.mockResolvedValueOnce(
      jsonResponse(
        runtimeSessionSnapshot({
          session_id: "session.0042",
          state: "awaiting_answer",
          mode: "Practice",
          session_intent: "Remediate",
          current_unit: {
            id: "elu.concept_recall.practice.remediate.concept.alpha-topic",
            visible_prompt: "Explain caching under stricter practice posture.",
          },
        }),
      ),
    );

    render(<App />);

    const answerField = (await screen.findByRole("textbox", {
      name: "Your answer",
    })) as HTMLTextAreaElement;
    expect(answerField.value).toBe("Draft answer kept in the browser.");
    expect(answerField.disabled).toBe(false);
    expect(
      screen.getByRole("heading", { name: "Practice / Remediate" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Explain caching under stricter practice posture."),
    ).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0]?.[0]).toContain("/runtime/sessions/session.0042");
  });

  it("restores an evaluation-pending session without resubmitting the answer", async () => {
    setStoredSessionEnvelope({
      sessionId: "session.0043",
      transcript: "Answer already submitted once.",
      answerSubmitted: true,
    });
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse(
          runtimeSessionSnapshot({
            session_id: "session.0043",
            state: "evaluation_pending",
            mode: "Study",
            session_intent: "LearnNew",
            current_unit: {
              id: "elu.concept_recall.study.learn_new.concept.alpha-topic",
              visible_prompt: "Explain caching.",
            },
          }),
        ),
      )
      .mockResolvedValueOnce(reviewPayload("session.0043"));

    render(<App />);

    expect(await screen.findByText("Weighted score")).toBeInTheDocument();
    expect(screen.getByText("0.67")).toBeInTheDocument();
    expect(window.localStorage.getItem(SESSION_RESUME_STORAGE_KEY)).toBeNull();

    const calls = fetchMock.mock.calls.map((call) => String(call[0]));
    expect(calls.filter((url) => url.includes("/runtime/sessions/session.0043/answer"))).toHaveLength(0);
    expect(calls.filter((url) => url.includes("/runtime/sessions/session.0043/evaluate"))).toHaveLength(1);
  });

  it("restores a reviewed session directly from backend review state", async () => {
    setStoredSessionEnvelope({
      sessionId: "session.0044",
      transcript: "Previously submitted answer.",
      answerSubmitted: true,
    });
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse(
          runtimeSessionSnapshot({
            session_id: "session.0044",
            state: "review_presented",
            mode: "Study",
            session_intent: "LearnNew",
            current_unit: {
              id: "elu.concept_recall.study.learn_new.concept.alpha-topic",
              visible_prompt: "Explain caching.",
            },
          }),
        ),
      )
      .mockResolvedValueOnce(reviewPayload("session.0044"));

    render(<App />);

    expect(await screen.findByText("Weighted score")).toBeInTheDocument();
    expect(screen.getByText("0.67")).toBeInTheDocument();
    expect(window.localStorage.getItem(SESSION_RESUME_STORAGE_KEY)).toBeNull();

    const calls = fetchMock.mock.calls.map((call) => String(call[0]));
    expect(calls.filter((url) => url.includes("/runtime/sessions/session.0044/answer"))).toHaveLength(0);
    expect(calls.filter((url) => url.includes("/runtime/sessions/session.0044/evaluate"))).toHaveLength(0);
    expect(calls.filter((url) => url.includes("/runtime/sessions/session.0044/review"))).toHaveLength(1);
  });

  it("clears a stale stored session and returns to the launcher", async () => {
    setStoredSessionEnvelope({
      sessionId: "session.missing",
      transcript: "Stale draft.",
      answerSubmitted: false,
    });
    fetchMock
      .mockResolvedValueOnce(errorResponse(404, "unknown session_id: session.missing"))
      .mockResolvedValueOnce(
        jsonResponse({
          decision_id: "rec.0001",
          policy_version: "bootstrap.recommendation.v1",
          decision_mode: "rule_based",
          candidate_actions: [],
          chosen_action: {
            mode: "Study",
            session_intent: "LearnNew",
            target_type: "concept",
            target_id: "concept.alpha-topic",
            difficulty_profile: "introductory",
            strictness_profile: "supportive",
            session_size: "single_unit",
            delivery_profile: "text_first",
            rationale: "Resume from launcher.",
          },
          supporting_signals: [],
          blocking_signals: [],
          rationale: "Resume from launcher.",
          alternatives_summary: "",
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          mode: "Study",
          session_intent: "LearnNew",
          items: [
            {
              unit_id: "elu.concept_recall.study.learn_new.concept.alpha-topic",
              content_id: "concept.alpha-topic",
              topic_slug: "alpha-topic",
              display_title: "Кэширование",
              visible_prompt: "Explain caching.",
              effective_difficulty: "introductory",
            },
          ],
        }),
      );

    render(<App />);

    expect(await screen.findByText("Backend-provided manual options")).toBeInTheDocument();
    expect(window.localStorage.getItem(SESSION_RESUME_STORAGE_KEY)).toBeNull();
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(3);
    });
    expect(fetchMock.mock.calls[0]?.[0]).toContain("/runtime/sessions/session.missing");
    expect(fetchMock.mock.calls[1]?.[0]).toContain("/recommendations/next");
    expect(fetchMock.mock.calls[2]?.[0]).toContain("/runtime/manual-launch-options");
  });

  it("clears the stored session envelope on manual reset", async () => {
    setStoredSessionEnvelope({
      sessionId: "session.0045",
      transcript: "Draft answer kept in the browser.",
      answerSubmitted: false,
    });
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse(
          runtimeSessionSnapshot({
            session_id: "session.0045",
            state: "awaiting_answer",
            mode: "Study",
            session_intent: "LearnNew",
            current_unit: {
              id: "elu.concept_recall.study.learn_new.concept.alpha-topic",
              visible_prompt: "Explain caching.",
            },
          }),
        ),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          decision_id: "rec.0002",
          policy_version: "bootstrap.recommendation.v1",
          decision_mode: "rule_based",
          candidate_actions: [],
          chosen_action: {
            mode: "Study",
            session_intent: "LearnNew",
            target_type: "concept",
            target_id: "concept.alpha-topic",
            difficulty_profile: "introductory",
            strictness_profile: "supportive",
            session_size: "single_unit",
            delivery_profile: "text_first",
            rationale: "Return to launcher.",
          },
          supporting_signals: [],
          blocking_signals: [],
          rationale: "Return to launcher.",
          alternatives_summary: "",
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          mode: "Study",
          session_intent: "LearnNew",
          items: [
            {
              unit_id: "elu.concept_recall.study.learn_new.concept.alpha-topic",
              content_id: "concept.alpha-topic",
              topic_slug: "alpha-topic",
              display_title: "Кэширование",
              visible_prompt: "Explain caching.",
              effective_difficulty: "introductory",
            },
          ],
        }),
      );

    render(<App />);

    await screen.findByRole("textbox", { name: "Your answer" });
    fireEvent.click(screen.getByRole("button", { name: "Back to launcher" }));

    expect(await screen.findByText("Backend-provided manual options")).toBeInTheDocument();
    expect(window.localStorage.getItem(SESSION_RESUME_STORAGE_KEY)).toBeNull();
  });

  it("shows an explicit restore error and retries the saved session", async () => {
    setStoredSessionEnvelope({
      sessionId: "session.0050",
      transcript: "Draft answer that should survive the failed restore.",
      answerSubmitted: false,
    });
    fetchMock
      .mockResolvedValueOnce(errorResponse(503, "temporary restore failure"))
      .mockResolvedValueOnce(
        jsonResponse(
          runtimeSessionSnapshot({
            session_id: "session.0050",
            state: "awaiting_answer",
            mode: "Study",
            session_intent: "LearnNew",
            current_unit: {
              id: "elu.concept_recall.study.learn_new.concept.alpha-topic",
              visible_prompt: "Explain caching after retry.",
            },
          }),
        ),
      );

    render(<App />);

    expect(await screen.findByText("temporary restore failure")).toBeInTheDocument();
    expect(window.localStorage.getItem(SESSION_RESUME_STORAGE_KEY)).not.toBeNull();
    expect(screen.queryByText("Backend-provided manual options")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Retry saved session" }));

    const answerField = (await screen.findByRole("textbox", {
      name: "Your answer",
    })) as HTMLTextAreaElement;
    expect(answerField.value).toBe("Draft answer that should survive the failed restore.");
    expect(screen.getByText("Explain caching after retry.")).toBeInTheDocument();
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(2);
    });
  });

  it("allows discarding a failed saved session and returning to the launcher", async () => {
    setStoredSessionEnvelope({
      sessionId: "session.0051",
      transcript: "Draft answer that will be discarded.",
      answerSubmitted: false,
    });
    fetchMock
      .mockResolvedValueOnce(errorResponse(503, "temporary restore failure"))
      .mockResolvedValueOnce(recommendationPayload("Discard and continue."))
      .mockResolvedValueOnce(manualLaunchOptionsPayload());

    render(<App />);

    expect(await screen.findByText("temporary restore failure")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Discard saved session" }));

    expect(await screen.findByText("Backend-provided manual options")).toBeInTheDocument();
    expect(window.localStorage.getItem(SESSION_RESUME_STORAGE_KEY)).toBeNull();
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(3);
    });
  });

  it("restores the shown recommendation from local storage without generating a new one", async () => {
    setStoredRecommendation(recommendationPayloadData("Resume the shown recommendation."));
    fetchMock.mockResolvedValueOnce(manualLaunchOptionsPayload());

    render(<App />);

    expect(await screen.findByText("Resume the shown recommendation.")).toBeInTheDocument();
    expect(screen.getByText("bootstrap.recommendation.v1")).toBeInTheDocument();
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });
    expect(fetchMock.mock.calls[0]?.[0]).toContain("/runtime/manual-launch-options");
  });
});

function jsonResponse(payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: {
      "Content-Type": "application/json",
    },
  });
}

function errorResponse(status: number, detail: string): Response {
  return new Response(JSON.stringify({ detail }), {
    status,
    headers: {
      "Content-Type": "application/json",
    },
  });
}

function setStoredSessionEnvelope(payload: {
  sessionId: string;
  transcript: string;
  answerSubmitted: boolean;
}): void {
  window.localStorage.setItem(SESSION_RESUME_STORAGE_KEY, JSON.stringify(payload));
}

function runtimeSessionSnapshot(payload: {
  session_id: string;
  state: string;
  mode: string;
  session_intent: string;
  current_unit: {
    id: string;
    visible_prompt: string;
  };
}): Record<string, unknown> {
  return {
    session_id: payload.session_id,
    user_id: "demo-user",
    mode: payload.mode,
    session_intent: payload.session_intent,
    strictness_profile: payload.mode === "Practice" ? "standard" : "supportive",
    state: payload.state,
    planned_unit_ids: [payload.current_unit.id],
    current_unit: payload.current_unit,
    event_ids: [],
    last_evaluation_result: null,
    last_review_report: null,
    recommendation_decision_id: null,
  };
}

function reviewPayload(sessionId: string): Response {
  return jsonResponse({
    session_id: sessionId,
    state: "review_presented",
    evaluation_result: {
      evaluation_id: "evaluation.0001",
      weighted_score: 0.67,
      overall_confidence: 0.74,
      missing_dimensions: ["trade_off_articulation"],
    },
    review_report: {
      strengths: ["The answer explains the concept itself in working terms."],
      missed_dimensions: ["Trade-off articulation"],
      reasoning_gaps: ["Trade-offs stay shallow."],
      recommended_next_focus: "Add the main trade-offs next time.",
      support_dependence_note: null,
    },
  });
}

function recommendationPayload(rationale: string): Response {
  return jsonResponse(recommendationPayloadData(rationale));
}

function recommendationPayloadData(rationale: string): Record<string, unknown> {
  return {
    decision_id: "rec.0001",
    policy_version: "bootstrap.recommendation.v1",
    decision_mode: "rule_based",
    candidate_actions: [],
    chosen_action: {
      mode: "Study",
      session_intent: "LearnNew",
      target_type: "concept",
      target_id: "concept.alpha-topic",
      difficulty_profile: "introductory",
      strictness_profile: "supportive",
      session_size: "single_unit",
      delivery_profile: "text_first",
      rationale,
    },
    supporting_signals: [],
    blocking_signals: [],
    rationale,
    alternatives_summary: "",
  };
}

function manualLaunchOptionsPayload(): Response {
  return jsonResponse({
    mode: "Study",
    session_intent: "LearnNew",
    items: [
      {
        unit_id: "elu.concept_recall.study.learn_new.concept.alpha-topic",
        content_id: "concept.alpha-topic",
        topic_slug: "alpha-topic",
        display_title: "Кэширование",
        visible_prompt: "Explain caching.",
        effective_difficulty: "introductory",
      },
    ],
  });
}

function setStoredRecommendation(payload: Record<string, unknown>): void {
  window.localStorage.setItem(RECOMMENDATION_STORAGE_KEY, JSON.stringify(payload));
}
