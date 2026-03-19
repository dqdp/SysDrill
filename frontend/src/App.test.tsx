import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

const fetchMock = vi.fn();

describe("App", () => {
  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  it("loads launch options and reaches review through the backend-driven flow", async () => {
    fetchMock
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

    expect(await screen.findByText("Кэширование")).toBeInTheDocument();
    const practiceRemediateRadio = screen.getByRole("radio", {
      name: /Practice \/ Remediate/i,
    });
    expect(practiceRemediateRadio).toBeEnabled();

    await waitFor(() => {
      expect(
        screen.getByRole("button", {
          name: "Start session",
        }),
      ).toBeEnabled();
    });

    fireEvent.click(screen.getByRole("button", { name: "Start session" }));

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
      expect(fetchMock).toHaveBeenCalledTimes(4);
    });
    expect(fetchMock.mock.calls[0]?.[0]).toContain("/runtime/manual-launch-options");
    expect(fetchMock.mock.calls[1]?.[0]).toContain("/runtime/sessions/manual-start");
  });

  it("shows backend errors explicitly on launcher load", async () => {
    fetchMock.mockResolvedValueOnce(errorResponse(503, "runtime content is not configured"));

    render(<App />);

    expect(
      await screen.findByText("runtime content is not configured"),
    ).toBeInTheDocument();
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
