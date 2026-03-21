import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

const fetchMock = vi.fn();

describe("App", () => {
  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
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
