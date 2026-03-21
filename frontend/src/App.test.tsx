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
    fetchMock.mockImplementation((input) => {
      const url = String(input);
      if (url.includes("/learner/summary")) {
        return Promise.resolve(learnerSummaryPayload());
      }
      throw new Error(`Unexpected fetch call: ${url}`);
    });
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
      .mockResolvedValueOnce(learnerSummaryPayload())
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
        jsonResponse(
          runtimeSessionSnapshot({
            session_id: "session.0001",
            state: "completed",
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
    expect((await screen.findAllByText("Кэширование")).length).toBeGreaterThan(0);
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
      expect(fetchMock).toHaveBeenCalledTimes(10);
    });
    const calls = fetchMock.mock.calls.map((call) => String(call[0]));
    expect(calls[0]).toContain("/recommendations/next");
    expect(calls[1]).toContain("/runtime/manual-launch-options");
    expect(calls[2]).toContain("/learner/summary");
    expect(calls[3]).toContain("/runtime/sessions/start-from-recommendation");
    expect(calls[6]).toContain("/runtime/sessions/session.0001/complete");
    expect(calls[7]).toContain("/recommendations/next");
    expect(calls[8]).toContain("/runtime/manual-launch-options");
    expect(calls[9]).toContain("/learner/summary");
  });

  it("runs a bounded mock follow-up loop from the manual launcher", async () => {
    fetchMock
      .mockResolvedValueOnce(recommendationPayload("Start here."))
      .mockResolvedValueOnce(manualLaunchOptionsPayload())
      .mockResolvedValueOnce(learnerSummaryPayload())
      .mockResolvedValueOnce(mockManualLaunchOptionsPayload())
      .mockResolvedValueOnce(
        jsonResponse({
          session_id: "session.0100",
          state: "awaiting_answer",
          current_unit: {
            id: "elu.scenario_readiness_check.mock_interview.readiness_check.scenario.url-shortener.basic",
            visible_prompt:
              "Design a URL Shortener for a read-heavy product with high availability requirements.",
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          session_id: "session.0100",
          state: "follow_up_round",
          current_unit: {
            id: "elu.scenario_readiness_check.mock_interview.readiness_check.scenario.url-shortener.basic",
            visible_prompt:
              "How would you generate short identifiers without creating avoidable collisions?",
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          session_id: "session.0100",
          state: "evaluation_pending",
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          session_id: "session.0100",
          state: "review_presented",
          evaluation_result: {
            evaluation_id: "evaluation.0100",
            weighted_score: 0.71,
            overall_confidence: 0.76,
            missing_dimensions: ["reliability_awareness"],
          },
          review_report: {
            strengths: ["The answer covered redirect reads, storage, and identifier generation."],
            missed_dimensions: ["Reliability awareness"],
            reasoning_gaps: ["Failure handling and abuse prevention stayed shallow."],
            recommended_next_focus:
              "Tighten reliability trade-offs and explain how id generation behaves under contention.",
            support_dependence_note: null,
            follow_up_handling_note:
              "Follow-up handling stayed concrete enough to defend the identifier strategy.",
          },
        }),
      );

    render(<App />);

    await screen.findByText("Start here.");

    fireEvent.click(
      await screen.findByRole("radio", {
        name: /Mock Interview \/ Readiness Check/i,
      }),
    );

    expect(
      await screen.findByText(
        "Design a URL Shortener for a read-heavy product with high availability requirements.",
      ),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Start session" }));

    expect(
      await screen.findByRole("textbox", { name: "Your answer" }),
    ).toBeInTheDocument();
    fireEvent.change(screen.getByRole("textbox", { name: "Your answer" }), {
      target: {
        value:
          "I would start with redirect reads, durable mapping storage, and short-id generation.",
      },
    });

    fireEvent.click(screen.getByRole("button", { name: "Request review" }));

    expect(
      await screen.findByText(
        "How would you generate short identifiers without creating avoidable collisions?",
      ),
    ).toBeInTheDocument();

    fireEvent.change(screen.getByRole("textbox", { name: "Your answer" }), {
      target: {
        value:
          "I would use a counter or random strategy with collision checks and cache the redirect path.",
      },
    });

    fireEvent.click(screen.getByRole("button", { name: "Request review" }));

    expect(await screen.findByText("0.71")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Follow-up handling stayed concrete enough to defend the identifier strategy.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Tighten reliability trade-offs and explain how id generation behaves under contention.",
      ),
    ).toBeInTheDocument();
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

  it("renders learner summary sections on the launcher", async () => {
    fetchMock
      .mockResolvedValueOnce(recommendationPayload("Start here."))
      .mockResolvedValueOnce(manualLaunchOptionsPayload());

    render(<App />);

    expect(await screen.findByText("Current evidence snapshot")).toBeInTheDocument();
    expect(
      screen.getByText("Mock readiness is still too uncertain"),
    ).toBeInTheDocument();
    expect((await screen.findAllByText("Кэширование")).length).toBeGreaterThan(0);
    const reviewDueCard = screen.getByText("Review due").closest("article");
    expect(reviewDueCard).not.toBeNull();
    expect(reviewDueCard).toHaveTextContent(
      "Recent evidence looks fragile enough that a review pass is due.",
    );
  });

  it("keeps the launcher usable when learner summary loading fails", async () => {
    fetchMock.mockImplementation((input) => {
      const url = String(input);
      if (url.includes("/learner/summary")) {
        return Promise.resolve(errorResponse(503, "learner summary unavailable"));
      }
      throw new Error(`Unexpected fetch call: ${url}`);
    });
    fetchMock
      .mockResolvedValueOnce(recommendationPayload("Start here."))
      .mockResolvedValueOnce(manualLaunchOptionsPayload());

    render(<App />);

    expect(await screen.findByText("learner summary unavailable")).toBeInTheDocument();
    expect(await screen.findByText("Start here.")).toBeInTheDocument();
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
      .mockResolvedValueOnce(learnerSummaryPayload())
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
    expect(window.localStorage.getItem(SESSION_RESUME_STORAGE_KEY)).not.toBeNull();

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
    expect(window.localStorage.getItem(SESSION_RESUME_STORAGE_KEY)).not.toBeNull();

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
      expect(fetchMock).toHaveBeenCalledTimes(4);
    });
    expect(fetchMock.mock.calls[0]?.[0]).toContain("/runtime/sessions/session.missing");
    expect(fetchMock.mock.calls[1]?.[0]).toContain("/recommendations/next");
    expect(fetchMock.mock.calls[2]?.[0]).toContain("/runtime/manual-launch-options");
    expect(fetchMock.mock.calls[3]?.[0]).toContain("/learner/summary");
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
        jsonResponse(
          runtimeSessionSnapshot({
            session_id: "session.0045",
            state: "abandoned",
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
    const calls = fetchMock.mock.calls.map((call) => String(call[0]));
    expect(
      calls.some((url) => url.includes("/runtime/sessions/session.0045/abandon")),
    ).toBe(true);
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
      expect(fetchMock).toHaveBeenCalledTimes(4);
    });
  });

  it("restores the shown recommendation from local storage without generating a new one", async () => {
    setStoredRecommendation(recommendationPayloadData("Resume the shown recommendation."));
    fetchMock.mockResolvedValueOnce(manualLaunchOptionsPayload());

    render(<App />);

    expect(await screen.findByText("Resume the shown recommendation.")).toBeInTheDocument();
    expect(screen.getByText("bootstrap.recommendation.v1")).toBeInTheDocument();
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(2);
    });
    expect(fetchMock.mock.calls[0]?.[0]).toContain("/runtime/manual-launch-options");
    expect(fetchMock.mock.calls[1]?.[0]).toContain("/learner/summary");
  });

  it("recovers from a stale cached recommendation by loading a fresh decision", async () => {
    setStoredRecommendation(recommendationPayloadData("Stale cached recommendation."));
    fetchMock
      .mockResolvedValueOnce(manualLaunchOptionsPayload())
      .mockResolvedValueOnce(learnerSummaryPayload())
      .mockResolvedValueOnce(errorResponse(404, "unknown decision_id: rec.0001"))
      .mockResolvedValueOnce(
        recommendationPayload("Fresh recommendation after stale cached decision."),
      );

    render(<App />);

    expect(await screen.findByText("Stale cached recommendation.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Start recommended session" }));

    expect(
      await screen.findByText(
        "The saved recommendation is no longer available. Loaded a fresh recommendation.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Fresh recommendation after stale cached decision."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("textbox", { name: "Your answer" })).not.toBeInTheDocument();
    expect(window.localStorage.getItem(RECOMMENDATION_STORAGE_KEY)).toContain(
      "Fresh recommendation after stale cached decision.",
    );
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(4);
    });
    expect(fetchMock.mock.calls[2]?.[0]).toContain(
      "/runtime/sessions/start-from-recommendation",
    );
    expect(fetchMock.mock.calls[3]?.[0]).toContain("/recommendations/next");
  });

  it("recovers from a stale cached recommendation after a stale 400 start failure", async () => {
    setStoredRecommendation(recommendationPayloadData("Stale cached recommendation."));
    fetchMock
      .mockResolvedValueOnce(manualLaunchOptionsPayload())
      .mockResolvedValueOnce(learnerSummaryPayload())
      .mockResolvedValueOnce(
        errorResponse(
          400,
          "recommendation action target_id 'concept.alpha-topic' is not currently resolvable",
        ),
      )
      .mockResolvedValueOnce(
        recommendationPayload("Fresh recommendation after stale 400 decision."),
      );

    render(<App />);

    expect(await screen.findByText("Stale cached recommendation.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Start recommended session" }));

    expect(
      await screen.findByText(
        "The saved recommendation is no longer available. Loaded a fresh recommendation.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Fresh recommendation after stale 400 decision."),
    ).toBeInTheDocument();
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(4);
    });
    expect(fetchMock.mock.calls[3]?.[0]).toContain("/recommendations/next");
  });

  it("does not refresh recommendation for non-stale 400 start failures", async () => {
    setStoredRecommendation(recommendationPayloadData("Saved recommendation."));
    fetchMock
      .mockResolvedValueOnce(manualLaunchOptionsPayload())
      .mockResolvedValueOnce(learnerSummaryPayload())
      .mockResolvedValueOnce(errorResponse(400, "decision_id does not belong to user_id"));

    render(<App />);

    expect(await screen.findByText("Saved recommendation.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Start recommended session" }));

    expect(
      (await screen.findAllByText("decision_id does not belong to user_id")).length,
    ).toBeGreaterThan(0);
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(3);
    });
    expect(screen.getByText("Saved recommendation.")).toBeInTheDocument();
  });

  it("retries recommended start after a lost response without fetching a fresh recommendation", async () => {
    setStoredRecommendation(recommendationPayloadData("Saved recommendation."));
    fetchMock
      .mockResolvedValueOnce(manualLaunchOptionsPayload())
      .mockResolvedValueOnce(learnerSummaryPayload())
      .mockRejectedValueOnce(new Error("Network error"))
      .mockResolvedValueOnce(
        jsonResponse({
          session_id: "session.0200",
          state: "awaiting_answer",
          mode: "Study",
          session_intent: "LearnNew",
          recommendation_decision_id: "rec.0001",
          current_unit: {
            id: "elu.concept_recall.study.learn_new.concept.alpha-topic",
            visible_prompt: "Explain caching.",
          },
        }),
      );

    render(<App />);

    expect(await screen.findByText("Saved recommendation.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Start recommended session" }));
    expect((await screen.findAllByText("Network error")).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole("button", { name: "Start recommended session" }));

    expect(
      await screen.findByRole("textbox", {
        name: "Your answer",
      }),
    ).toBeInTheDocument();
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(4);
    });
    const calls = fetchMock.mock.calls.map((call) => String(call[0]));
    expect(calls.filter((url) => url.includes("/recommendations/next"))).toHaveLength(0);
    expect(calls.filter((url) => url.includes("/runtime/sessions/start-from-recommendation"))).toHaveLength(2);
  });

  it("routes a replayed recommended start into review recovery", async () => {
    setStoredRecommendation(recommendationPayloadData("Saved recommendation."));
    fetchMock
      .mockResolvedValueOnce(manualLaunchOptionsPayload())
      .mockResolvedValueOnce(learnerSummaryPayload())
      .mockRejectedValueOnce(new Error("Network error"))
      .mockResolvedValueOnce(
        jsonResponse(
          runtimeSessionSnapshot({
            session_id: "session.0201",
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
      .mockResolvedValueOnce(
        jsonResponse(
          runtimeSessionSnapshot({
            session_id: "session.0201",
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
      .mockResolvedValueOnce(reviewPayload("session.0201"));

    render(<App />);

    expect(await screen.findByText("Saved recommendation.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Start recommended session" }));
    expect((await screen.findAllByText("Network error")).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole("button", { name: "Start recommended session" }));

    expect(await screen.findByText("Weighted score")).toBeInTheDocument();
    expect(screen.getByText("0.67")).toBeInTheDocument();
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(6);
    });
    const calls = fetchMock.mock.calls.map((call) => String(call[0]));
    expect(calls.filter((url) => url.includes("/recommendations/next"))).toHaveLength(0);
    expect(calls.filter((url) => url.endsWith("/runtime/sessions/session.0201"))).toHaveLength(1);
    expect(calls.filter((url) => url.includes("/runtime/sessions/session.0201/review"))).toHaveLength(1);
  });

  it("returns to launcher and loads a fresh recommendation when replayed start is already terminal", async () => {
    setStoredRecommendation(recommendationPayloadData("Saved recommendation."));
    fetchMock
      .mockResolvedValueOnce(manualLaunchOptionsPayload())
      .mockResolvedValueOnce(learnerSummaryPayload())
      .mockRejectedValueOnce(new Error("Network error"))
      .mockResolvedValueOnce(
        jsonResponse(
          runtimeSessionSnapshot({
            session_id: "session.0202",
            state: "completed",
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
        jsonResponse(
          runtimeSessionSnapshot({
            session_id: "session.0202",
            state: "completed",
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
        recommendationPayload("Fresh recommendation after terminal replay."),
      )
      .mockResolvedValueOnce(manualLaunchOptionsPayload())
      .mockResolvedValueOnce(learnerSummaryPayload());

    render(<App />);

    expect(await screen.findByText("Saved recommendation.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Start recommended session" }));
    expect((await screen.findAllByText("Network error")).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole("button", { name: "Start recommended session" }));

    expect(
      await screen.findByText("Fresh recommendation after terminal replay."),
    ).toBeInTheDocument();
    expect(screen.getByText("Backend-provided manual options")).toBeInTheDocument();
    expect(window.localStorage.getItem(RECOMMENDATION_STORAGE_KEY)).toContain(
      "Fresh recommendation after terminal replay.",
    );
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(8);
    });
    const calls = fetchMock.mock.calls.map((call) => String(call[0]));
    expect(calls.filter((url) => url.includes("/recommendations/next"))).toHaveLength(1);
    expect(calls.filter((url) => url.endsWith("/runtime/sessions/session.0202"))).toHaveLength(1);
  });

  it("smoke-tests reload recovery through review and back to the launcher", async () => {
    setStoredSessionEnvelope({
      sessionId: "session.0090",
      transcript: "Caching reduces latency for repeated reads.",
      answerSubmitted: false,
    });
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse(
          runtimeSessionSnapshot({
            session_id: "session.0090",
            state: "awaiting_answer",
            mode: "Study",
            session_intent: "LearnNew",
            current_unit: {
              id: "elu.concept_recall.study.learn_new.concept.alpha-topic",
              visible_prompt: "Explain caching after reload.",
            },
          }),
        ),
      )
      .mockResolvedValueOnce(jsonResponse({ state: "evaluation_pending" }))
      .mockResolvedValueOnce(
        jsonResponse({
          session_id: "session.0090",
          state: "review_presented",
          evaluation_result: {
            evaluation_id: "evaluation.0090",
            weighted_score: 0.71,
            overall_confidence: 0.77,
            missing_dimensions: ["trade_off_articulation"],
          },
          review_report: {
            strengths: ["Explains the latency benefit clearly."],
            missed_dimensions: ["Trade-off articulation"],
            reasoning_gaps: ["Invalidation costs are omitted."],
            recommended_next_focus: "Call out invalidation and consistency trade-offs.",
            support_dependence_note: null,
          },
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse(
          runtimeSessionSnapshot({
            session_id: "session.0090",
            state: "completed",
            mode: "Study",
            session_intent: "LearnNew",
            current_unit: {
              id: "elu.concept_recall.study.learn_new.concept.alpha-topic",
              visible_prompt: "Explain caching after reload.",
            },
          }),
        ),
      )
      .mockResolvedValueOnce(recommendationPayload("Next step after recovered review."))
      .mockResolvedValueOnce(manualLaunchOptionsPayload());

    render(<App />);

    const restoredAnswer = (await screen.findByRole("textbox", {
      name: "Your answer",
    })) as HTMLTextAreaElement;
    expect(restoredAnswer.value).toBe("Caching reduces latency for repeated reads.");
    expect(screen.getByText("Explain caching after reload.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Request review" }));

    expect(await screen.findByText("Weighted score")).toBeInTheDocument();
    expect(screen.getByText("0.71")).toBeInTheDocument();
    expect(
      screen.getByText("Call out invalidation and consistency trade-offs."),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Back to launcher" }));

    expect(await screen.findByText("Backend-provided manual options")).toBeInTheDocument();
    expect(window.localStorage.getItem(SESSION_RESUME_STORAGE_KEY)).toBeNull();
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(7);
    });
    expect(fetchMock.mock.calls[0]?.[0]).toContain("/runtime/sessions/session.0090");
    expect(fetchMock.mock.calls[1]?.[0]).toContain("/runtime/sessions/session.0090/answer");
    expect(fetchMock.mock.calls[2]?.[0]).toContain("/runtime/sessions/session.0090/evaluate");
    expect(fetchMock.mock.calls[3]?.[0]).toContain("/runtime/sessions/session.0090/complete");
    expect(fetchMock.mock.calls[6]?.[0]).toContain("/learner/summary");
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

function mockManualLaunchOptionsPayload(): Response {
  return jsonResponse({
    mode: "MockInterview",
    session_intent: "ReadinessCheck",
    items: [
      {
        unit_id:
          "elu.scenario_readiness_check.mock_interview.readiness_check.scenario.url-shortener.basic",
        content_id: "scenario.url-shortener.basic",
        topic_slug: "url-shortener",
        display_title: "Design a URL Shortener",
        visible_prompt:
          "Design a URL Shortener for a read-heavy product with high availability requirements.",
        effective_difficulty: "standard",
      },
    ],
  });
}

function learnerSummaryPayload(): Response {
  return jsonResponse(learnerSummaryPayloadData());
}

function learnerSummaryPayloadData(): Record<string, unknown> {
  return {
    user_id: "demo-user",
    weak_areas: [
      {
        target_kind: "concept",
        target_id: "concept.alpha-topic",
        title: "Кэширование",
        posture: "weak",
        summary: "Reviewed evidence still points to a weak concept foundation here.",
      },
    ],
    review_due: [
      {
        target_kind: "concept",
        target_id: "concept.alpha-topic",
        title: "Кэширование",
        summary: "Recent evidence looks fragile enough that a review pass is due.",
      },
    ],
    readiness_summary: {
      category: "insufficient_evidence",
      title: "Mock readiness is still too uncertain",
      detail: "Need more completed practice evidence before escalating to a readiness check.",
    },
    evidence_posture: {
      category: "conservative_summary",
      title: "The learner summary stays intentionally conservative",
      details: [
        "Recent work still shows support-dependent evidence.",
        "The current summary is still based on limited repeated evidence.",
      ],
    },
  };
}

function setStoredRecommendation(payload: Record<string, unknown>): void {
  window.localStorage.setItem(RECOMMENDATION_STORAGE_KEY, JSON.stringify(payload));
}
