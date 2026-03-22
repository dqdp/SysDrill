import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ReviewShell } from "./ReviewShell";

describe("ReviewShell", () => {
  it("renders the review metrics and notes from a bounded mock evaluation", () => {
    render(
      <ReviewShell
        review={{
          session_id: "session.3000",
          state: "review_presented",
          evaluation_result: {
            evaluation_id: "evaluation.3000",
            weighted_score: 0.58,
            overall_confidence: 0.77,
            missing_dimensions: ["failure_handling"],
          },
          review_report: {
            strengths: ["The limiter algorithm fits the fairness constraint."],
            missed_dimensions: ["Failure handling"],
            reasoning_gaps: ["Degraded behavior under stale state is underspecified."],
            recommended_next_focus:
              "Clarify degraded behavior when the shared state store lags.",
            follow_up_handling_note:
              "The follow-up recovered some detail, but outage handling remained weak.",
            support_dependence_note:
              "The answer improved after the follow-up prompt instead of covering the issue proactively.",
          },
        }}
      />,
    );

    expect(screen.getByText("Weighted score")).toBeInTheDocument();
    expect(screen.getByText("0.58")).toBeInTheDocument();
    expect(screen.getByText("0.77")).toBeInTheDocument();
    expect(
      screen.getByText("Clarify degraded behavior when the shared state store lags."),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "The follow-up recovered some detail, but outage handling remained weak.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "The answer improved after the follow-up prompt instead of covering the issue proactively.",
      ),
    ).toBeInTheDocument();
  });
});
