import type { RecommendationDecisionResponse } from "./api";

export const RECOMMENDATION_STORAGE_KEY = "sysdrill.launcherRecommendation.v1";

export function readStoredRecommendation(): RecommendationDecisionResponse | null {
  const rawValue = window.localStorage.getItem(RECOMMENDATION_STORAGE_KEY);
  if (!rawValue) {
    return null;
  }

  try {
    const parsed = JSON.parse(rawValue) as Partial<RecommendationDecisionResponse>;
    if (
      typeof parsed.decision_id === "string" &&
      typeof parsed.policy_version === "string" &&
      typeof parsed.decision_mode === "string" &&
      typeof parsed.rationale === "string" &&
      parsed.chosen_action !== undefined &&
      typeof parsed.chosen_action === "object" &&
      parsed.chosen_action !== null &&
      typeof parsed.chosen_action.mode === "string" &&
      typeof parsed.chosen_action.session_intent === "string" &&
      typeof parsed.chosen_action.target_type === "string" &&
      typeof parsed.chosen_action.target_id === "string" &&
      typeof parsed.chosen_action.difficulty_profile === "string" &&
      typeof parsed.chosen_action.strictness_profile === "string" &&
      typeof parsed.chosen_action.session_size === "string" &&
      typeof parsed.chosen_action.delivery_profile === "string" &&
      typeof parsed.chosen_action.rationale === "string" &&
      Array.isArray(parsed.candidate_actions) &&
      Array.isArray(parsed.supporting_signals) &&
      Array.isArray(parsed.blocking_signals)
    ) {
      return parsed as RecommendationDecisionResponse;
    }
  } catch {
    // Ignore malformed client-side recommendation state and fall back to a clean fetch.
  }

  clearStoredRecommendation();
  return null;
}

export function writeStoredRecommendation(
  recommendation: RecommendationDecisionResponse,
): void {
  window.localStorage.setItem(
    RECOMMENDATION_STORAGE_KEY,
    JSON.stringify(recommendation),
  );
}

export function clearStoredRecommendation(): void {
  window.localStorage.removeItem(RECOMMENDATION_STORAGE_KEY);
}
