export type SessionShellProps = {
  answerSubmitted: boolean;
  onSubmitAnswer: () => void;
  onTranscriptChange: (value: string) => void;
  phase: "session" | "submitting";
  sessionError: string;
  transcript: string;
  visiblePrompt: string;
};

export function SessionShell({
  answerSubmitted,
  onSubmitAnswer,
  onTranscriptChange,
  phase,
  sessionError,
  transcript,
  visiblePrompt,
}: SessionShellProps) {
  return (
    <div className="session-section">
      <p className="panel-label">Prompt</p>
      <blockquote className="prompt-card">{visiblePrompt}</blockquote>
      <label className="answer-field">
        <span>Your answer</span>
        <textarea
          disabled={answerSubmitted}
          onChange={(event) => onTranscriptChange(event.target.value)}
          placeholder="Explain the concept in your own words, when to use it, and the trade-offs."
          rows={10}
          value={transcript}
        />
      </label>
      {sessionError ? <p className="error-banner">{sessionError}</p> : null}
      <button
        className="primary-button"
        disabled={phase === "submitting"}
        onClick={onSubmitAnswer}
        type="button"
      >
        {phase === "submitting" ? "Submitting and evaluating..." : "Request review"}
      </button>
    </div>
  );
}
