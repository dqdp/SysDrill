import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ProfileSelector } from "./ProfileSelector";

const profiles = [
  {
    mode: "Study",
    sessionIntent: "LearnNew",
    label: "Study / Learn New",
    description: "Supportive recall over a single concept.",
  },
  {
    mode: "MockInterview",
    sessionIntent: "ReadinessCheck",
    label: "Mock Interview / Readiness Check",
    description: "One bounded scenario pass with a single follow-up probe.",
  },
] as const;

describe("ProfileSelector", () => {
  it("lets the launcher switch profiles while the shell is idle", () => {
    const onProfileChange = vi.fn();

    render(
      <ProfileSelector
        isLauncherPhase
        onProfileChange={onProfileChange}
        profiles={profiles}
        selectedProfileIndex={1}
      />,
    );

    fireEvent.click(screen.getByRole("radio", { name: /Study \/ Learn New/i }));

    expect(onProfileChange).toHaveBeenCalledWith(0);
  });

  it("keeps the profiles visible but disabled outside launcher phase", () => {
    render(
      <ProfileSelector
        isLauncherPhase={false}
        onProfileChange={vi.fn()}
        profiles={profiles}
        selectedProfileIndex={1}
      />,
    );

    expect(
      screen.getByRole("radio", { name: /Mock Interview \/ Readiness Check/i }),
    ).toBeDisabled();
    expect(screen.getByRole("radio", { name: /Study \/ Learn New/i })).toBeDisabled();
  });
});
