import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SessionShell } from "./SessionShell";

describe("SessionShell", () => {
  it("renders the active prompt, transcript, and submit action", () => {
    const onTranscriptChange = vi.fn();
    const onSubmitAnswer = vi.fn();

    render(
      <SessionShell
        answerSubmitted={false}
        onSubmitAnswer={onSubmitAnswer}
        onTranscriptChange={onTranscriptChange}
        phase="session"
        sessionError=""
        transcript="Burst traffic should still preserve tenant fairness."
        visiblePrompt="Design a Rate Limiter for a multi-tenant API."
      />,
    );

    expect(
      screen.getByText("Design a Rate Limiter for a multi-tenant API."),
    ).toBeInTheDocument();

    fireEvent.change(screen.getByRole("textbox", { name: "Your answer" }), {
      target: { value: "Revised answer" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Request review" }));

    expect(onTranscriptChange).toHaveBeenCalledWith("Revised answer");
    expect(onSubmitAnswer).toHaveBeenCalledTimes(1);
  });

  it("shows the submitting state and disables the textarea once the answer is locked", () => {
    render(
      <SessionShell
        answerSubmitted
        onSubmitAnswer={vi.fn()}
        onTranscriptChange={vi.fn()}
        phase="submitting"
        sessionError="Evaluation is still loading."
        transcript="Locked answer"
        visiblePrompt="Follow-up: how does degraded mode behave if Redis lags?"
      />,
    );

    expect(screen.getByText("Evaluation is still loading.")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Your answer" })).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Submitting and evaluating..." }),
    ).toBeDisabled();
  });
});
