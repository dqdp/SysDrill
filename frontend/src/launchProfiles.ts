export const LAUNCH_PROFILES = [
  {
    mode: "Study",
    sessionIntent: "LearnNew",
    label: "Study / Learn New",
    description: "Supportive recall over a single concept.",
  },
  {
    mode: "Study",
    sessionIntent: "Reinforce",
    label: "Study / Reinforce",
    description: "Repeat concept recall with the same bounded format.",
  },
  {
    mode: "Study",
    sessionIntent: "SpacedReview",
    label: "Study / Spaced Review",
    description: "Use the same concept-recall loop for review-oriented sessions.",
  },
  {
    mode: "Practice",
    sessionIntent: "Reinforce",
    label: "Practice / Reinforce",
    description: "Slightly stricter recall drill using practice posture.",
  },
  {
    mode: "Practice",
    sessionIntent: "Remediate",
    label: "Practice / Remediate",
    description: "Targeted concept-recall remediation with lower support.",
  },
  {
    mode: "MockInterview",
    sessionIntent: "ReadinessCheck",
    label: "Mock Interview / Readiness Check",
    description: "One bounded scenario pass with a single follow-up probe.",
  },
] as const;

export type LaunchProfile = (typeof LAUNCH_PROFILES)[number];

export function profileIndexFor(mode: string, sessionIntent: string): number {
  const index = LAUNCH_PROFILES.findIndex(
    (profile) =>
      profile.mode === mode && profile.sessionIntent === sessionIntent,
  );

  return index >= 0 ? index : 0;
}
