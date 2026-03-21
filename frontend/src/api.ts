export type LaunchOption = {
  unit_id: string;
  content_id: string | null;
  topic_slug: string | null;
  display_title: string | null;
  visible_prompt: string;
  effective_difficulty: string;
};

export type LaunchOptionsResponse = {
  mode: string;
  session_intent: string;
  items: LaunchOption[];
};

export type RecommendationAction = {
  mode: string;
  session_intent: string;
  target_type: string;
  target_id: string;
  difficulty_profile: string;
  strictness_profile: string;
  session_size: string;
  delivery_profile: string;
};

export type RecommendationChosenAction = RecommendationAction & {
  rationale: string;
};

export type RecommendationDecisionResponse = {
  decision_id: string;
  policy_version: string;
  decision_mode: string;
  candidate_actions: RecommendationAction[];
  chosen_action: RecommendationChosenAction;
  supporting_signals: string[];
  blocking_signals: string[];
  rationale: string;
  alternatives_summary?: string;
};

export type ManualSessionResponse = {
  session_id: string;
  state: string;
  recommendation_decision_id?: string | null;
  current_unit: {
    id: string;
    visible_prompt: string;
  };
};

export type EvaluateResponse = {
  session_id: string;
  state: string;
  evaluation_result: {
    evaluation_id: string;
    weighted_score: number;
    overall_confidence: number;
    missing_dimensions: string[];
  };
  review_report: {
    strengths: string[];
    missed_dimensions: string[];
    reasoning_gaps: string[];
    recommended_next_focus: string;
    support_dependence_note?: string | null;
  };
};

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new Error(detail);
  }

  return (await response.json()) as T;
}

async function readErrorDetail(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: string };
    if (typeof payload.detail === "string" && payload.detail) {
      return payload.detail;
    }
  } catch {
    return `${response.status} ${response.statusText}`;
  }

  return `${response.status} ${response.statusText}`;
}

export async function getManualLaunchOptions(
  mode: string,
  sessionIntent: string,
): Promise<LaunchOptionsResponse> {
  const params = new URLSearchParams({
    mode,
    session_intent: sessionIntent,
  });
  return request<LaunchOptionsResponse>(`/runtime/manual-launch-options?${params.toString()}`);
}

export async function startManualSession(
  mode: string,
  sessionIntent: string,
  unitId: string,
): Promise<ManualSessionResponse> {
  return request<ManualSessionResponse>("/runtime/sessions/manual-start", {
    method: "POST",
    body: JSON.stringify({
      user_id: "demo-user",
      mode,
      session_intent: sessionIntent,
      unit_id: unitId,
      source: "web",
    }),
  });
}

export async function getNextRecommendation(): Promise<RecommendationDecisionResponse> {
  return request<RecommendationDecisionResponse>("/recommendations/next", {
    method: "POST",
    body: JSON.stringify({
      user_id: "demo-user",
    }),
  });
}

export async function startRecommendedSession(
  decisionId: string,
  action: RecommendationChosenAction,
): Promise<ManualSessionResponse> {
  return request<ManualSessionResponse>("/runtime/sessions/start-from-recommendation", {
    method: "POST",
    body: JSON.stringify({
      user_id: "demo-user",
      decision_id: decisionId,
      action,
      source: "web",
    }),
  });
}

export async function submitAnswer(
  sessionId: string,
  transcript: string,
): Promise<void> {
  await request(`/runtime/sessions/${sessionId}/answer`, {
    method: "POST",
    body: JSON.stringify({
      transcript,
      response_modality: "text",
      submission_kind: "manual_submit",
    }),
  });
}

export async function evaluateSession(sessionId: string): Promise<EvaluateResponse> {
  return request<EvaluateResponse>(`/runtime/sessions/${sessionId}/evaluate`, {
    method: "POST",
  });
}
