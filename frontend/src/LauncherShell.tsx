import type {
  LaunchOption,
  LearnerSummaryResponse,
  RecommendationDecisionResponse,
} from "./api";

export type LauncherShellProps = {
  restoreError: string;
  recommendation: RecommendationDecisionResponse | null;
  recommendationError: string;
  isLoadingRecommendation: boolean;
  learnerSummary: LearnerSummaryResponse | null;
  summaryError: string;
  isLoadingSummary: boolean;
  launchOptions: LaunchOption[];
  launcherError: string;
  isLoadingOptions: boolean;
  selectedUnitId: string;
  sessionError: string;
  isStartingSession: boolean;
  onStartRecommendedSession: () => void;
  onSelectUnit: (unitId: string) => void;
  onStartSession: () => void;
  onRetryRestore: () => void;
  onDiscardSavedSession: () => void;
};

export function LauncherShell({
  restoreError,
  recommendation,
  recommendationError,
  isLoadingRecommendation,
  learnerSummary,
  summaryError,
  isLoadingSummary,
  launchOptions,
  launcherError,
  isLoadingOptions,
  selectedUnitId,
  sessionError,
  isStartingSession,
  onStartRecommendedSession,
  onSelectUnit,
  onStartSession,
  onRetryRestore,
  onDiscardSavedSession,
}: LauncherShellProps) {
  const learnerWeakAreas = Array.isArray(learnerSummary?.weak_areas)
    ? learnerSummary.weak_areas
    : [];
  const learnerReviewDue = Array.isArray(learnerSummary?.review_due)
    ? learnerSummary.review_due
    : [];
  const learnerEvidenceDetails = Array.isArray(learnerSummary?.evidence_posture?.details)
    ? learnerSummary.evidence_posture.details
    : [];

  return (
    <>
      {restoreError ? (
        <div className="launcher-section">
          <p className="error-banner">{restoreError}</p>
          <button className="primary-button" onClick={onRetryRestore} type="button">
            Retry saved session
          </button>
          <button className="ghost-button" onClick={onDiscardSavedSession} type="button">
            Discard saved session
          </button>
        </div>
      ) : null}

      {!restoreError ? (
        <div className="launcher-section">
          <div className="launcher-header">
            <div>
              <p className="panel-label">Recommended next step</p>
              <h3>Deterministic recommendation</h3>
            </div>
            <span className="status-chip">
              {isLoadingRecommendation
                ? "Loading"
                : recommendation?.policy_version ?? "Unavailable"}
            </span>
          </div>

          {recommendationError ? (
            <p className="error-banner">{recommendationError}</p>
          ) : null}

          {recommendation ? (
            <blockquote className="prompt-card">
              <p className="panel-label">
                {recommendation.chosen_action.mode} /{" "}
                {recommendation.chosen_action.session_intent}
              </p>
              <p>{recommendation.rationale}</p>
            </blockquote>
          ) : null}

          {sessionError ? <p className="error-banner">{sessionError}</p> : null}

          <button
            className="primary-button"
            disabled={isLoadingRecommendation || isStartingSession || !recommendation}
            onClick={onStartRecommendedSession}
            type="button"
          >
            {isStartingSession ? "Starting session..." : "Start recommended session"}
          </button>
        </div>
      ) : null}

      {!restoreError ? (
        <div className="launcher-section">
          <div className="launcher-header">
            <div>
              <p className="panel-label">Learner summary</p>
              <h3>Current evidence snapshot</h3>
            </div>
            <span className="status-chip">
              {isLoadingSummary
                ? "Loading"
                : learnerSummary
                  ? `${learnerWeakAreas.length} weak / ${learnerReviewDue.length} due`
                  : "Unavailable"}
            </span>
          </div>

          {summaryError ? <p className="error-banner">{summaryError}</p> : null}

          {learnerSummary ? (
            <div className="review-grid">
              <article className="review-card emphasis">
                <p className="panel-label">Readiness</p>
                <strong>
                  {learnerSummary.readiness_summary?.title ?? "Summary unavailable"}
                </strong>
                <p>
                  {learnerSummary.readiness_summary?.detail ??
                    "Learner readiness could not be summarized right now."}
                </p>
              </article>

              <article className="review-card">
                <p className="panel-label">Weak areas</p>
                {learnerWeakAreas.length > 0 ? (
                  <ul>
                    {learnerWeakAreas.map((item) => (
                      <li key={`${item.target_kind}-${item.target_id}`}>
                        <strong>{item.title}</strong>: {item.summary}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="empty-state">
                    No weak areas are strongly evidenced yet.
                  </p>
                )}
              </article>

              <article className="review-card">
                <p className="panel-label">Review due</p>
                {learnerReviewDue.length > 0 ? (
                  <ul>
                    {learnerReviewDue.map((item) => (
                      <li key={`${item.target_kind}-${item.target_id}`}>
                        <strong>{item.title}</strong>: {item.summary}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="empty-state">Nothing is strongly review-due yet.</p>
                )}
              </article>

              <article className="review-card">
                <p className="panel-label">Evidence posture</p>
                <strong>
                  {learnerSummary.evidence_posture?.title ?? "Summary unavailable"}
                </strong>
                <ul>
                  {learnerEvidenceDetails.map((detail) => (
                    <li key={detail}>{detail}</li>
                  ))}
                </ul>
              </article>
            </div>
          ) : null}
        </div>
      ) : null}

      {!restoreError ? (
        <div className="launcher-section">
          <div className="launcher-header">
            <div>
              <p className="panel-label">Launchable units</p>
              <h3>Backend-provided manual options</h3>
            </div>
            <span className="status-chip">
              {isLoadingOptions ? "Loading" : `${launchOptions.length} options`}
            </span>
          </div>

          {launcherError ? <p className="error-banner">{launcherError}</p> : null}

          {!isLoadingOptions && !launcherError && launchOptions.length === 0 ? (
            <p className="empty-state">
              No launchable units are currently available for this mode and intent
              combination.
            </p>
          ) : null}

          <div className="launch-option-list">
            {launchOptions.map((option) => {
              const checked = option.unit_id === selectedUnitId;
              return (
                <label
                  className={`launch-option${checked ? " selected" : ""}`}
                  key={option.unit_id}
                >
                  <input
                    checked={checked}
                    name="launch-option"
                    onChange={() => onSelectUnit(option.unit_id)}
                    type="radio"
                  />
                  <div className="launch-option-copy">
                    <div className="launch-option-topline">
                      <strong>
                        {option.display_title ?? option.topic_slug ?? option.unit_id}
                      </strong>
                      <span>{option.effective_difficulty}</span>
                    </div>
                    <p>{option.visible_prompt}</p>
                  </div>
                </label>
              );
            })}
          </div>

          {sessionError ? <p className="error-banner">{sessionError}</p> : null}

          <button
            className="primary-button"
            disabled={isLoadingOptions || isStartingSession || !selectedUnitId}
            onClick={onStartSession}
            type="button"
          >
            {isStartingSession ? "Starting session..." : "Start session"}
          </button>
        </div>
      ) : null}
    </>
  );
}
