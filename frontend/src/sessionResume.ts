export const SESSION_RESUME_STORAGE_KEY = "sysdrill.activeSession.v1";

export type SessionResumeEnvelope = {
  sessionId: string;
  transcript: string;
  answerSubmitted: boolean;
};

export function readSessionResumeEnvelope(): SessionResumeEnvelope | null {
  const rawValue = window.localStorage.getItem(SESSION_RESUME_STORAGE_KEY);
  if (!rawValue) {
    return null;
  }

  try {
    const parsed = JSON.parse(rawValue) as Partial<SessionResumeEnvelope>;
    if (
      typeof parsed.sessionId === "string" &&
      parsed.sessionId &&
      typeof parsed.transcript === "string" &&
      typeof parsed.answerSubmitted === "boolean"
    ) {
      return {
        sessionId: parsed.sessionId,
        transcript: parsed.transcript,
        answerSubmitted: parsed.answerSubmitted,
      };
    }
  } catch {
    // Ignore malformed client-side resume state and fall back to a clean launcher.
  }

  window.localStorage.removeItem(SESSION_RESUME_STORAGE_KEY);
  return null;
}

export function writeSessionResumeEnvelope(payload: SessionResumeEnvelope): void {
  window.localStorage.setItem(SESSION_RESUME_STORAGE_KEY, JSON.stringify(payload));
}

export function clearSessionResumeEnvelope(): void {
  window.localStorage.removeItem(SESSION_RESUME_STORAGE_KEY);
}
