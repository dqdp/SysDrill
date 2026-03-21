import { startTransition, useEffect, useState } from "react";

import {
  abandonRuntimeSession,
  ApiError,
  completeRuntimeSession,
  evaluateSession,
  getLearnerSummary,
  getRuntimeSession,
  getReview,
  getNextRecommendation,
  getManualLaunchOptions,
  startRecommendedSession,
  startManualSession,
  submitAnswer,
  type EvaluateResponse,
  type LaunchOption,
  type LearnerSummaryResponse,
  type RecommendationDecisionResponse,
  type RuntimeSessionResponse,
} from "./api";
import {
  clearSessionResumeEnvelope,
  readSessionResumeEnvelope,
  writeSessionResumeEnvelope,
} from "./sessionResume";
import {
  clearStoredRecommendation,
  readStoredRecommendation,
  writeStoredRecommendation,
} from "./recommendationResume";

const LAUNCH_PROFILES = [
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
] as const;

type Phase = "launcher" | "session" | "submitting" | "review";

export function App() {
  const [profileIndex, setProfileIndex] = useState(0);
  const [recommendation, setRecommendation] =
    useState<RecommendationDecisionResponse | null>(null);
  const [recommendationError, setRecommendationError] = useState("");
  const [isLoadingRecommendation, setIsLoadingRecommendation] = useState(true);
  const [recommendationReloadKey, setRecommendationReloadKey] = useState(0);
  const [restoreAttemptKey, setRestoreAttemptKey] = useState(0);
  const [restoreError, setRestoreError] = useState("");
  const [learnerSummary, setLearnerSummary] = useState<LearnerSummaryResponse | null>(null);
  const [summaryError, setSummaryError] = useState("");
  const [launchOptions, setLaunchOptions] = useState<LaunchOption[]>([]);
  const [selectedUnitId, setSelectedUnitId] = useState<string>("");
  const [launcherError, setLauncherError] = useState<string>("");
  const [phase, setPhase] = useState<Phase>("launcher");
  const [isLoadingOptions, setIsLoadingOptions] = useState(true);
  const [isLoadingSummary, setIsLoadingSummary] = useState(true);
  const [isRestoringSession, setIsRestoringSession] = useState(true);
  const [isStartingSession, setIsStartingSession] = useState(false);
  const [isReturningToLauncher, setIsReturningToLauncher] = useState(false);
  const [sessionId, setSessionId] = useState("");
  const [visiblePrompt, setVisiblePrompt] = useState("");
  const [transcript, setTranscript] = useState("");
  const [answerSubmitted, setAnswerSubmitted] = useState(false);
  const [sessionError, setSessionError] = useState("");
  const [review, setReview] = useState<EvaluateResponse | null>(null);

  const activeProfile = LAUNCH_PROFILES[profileIndex] ?? LAUNCH_PROFILES[0];
  const isLauncherPhase = phase === "launcher";
  const shouldLoadLauncherData = isLauncherPhase && !isRestoringSession && !restoreError;
  const learnerWeakAreas = Array.isArray(learnerSummary?.weak_areas)
    ? learnerSummary.weak_areas
    : [];
  const learnerReviewDue = Array.isArray(learnerSummary?.review_due)
    ? learnerSummary.review_due
    : [];
  const learnerEvidenceDetails = Array.isArray(learnerSummary?.evidence_posture?.details)
    ? learnerSummary.evidence_posture.details
    : [];

  useEffect(() => {
    let cancelled = false;

    async function restoreSession() {
      const envelope = readSessionResumeEnvelope();
      if (envelope === null) {
        if (cancelled) {
          return;
        }
        startTransition(() => {
          setRestoreError("");
          setIsRestoringSession(false);
        });
        return;
      }

      try {
        const session = await getRuntimeSession(envelope.sessionId);

        if (cancelled) {
          return;
        }

        if (isPreAnswerState(session.state)) {
          startTransition(() => {
            applySessionState({
              answerSubmitted: false,
              phase: "session",
              profileIndex: profileIndexFor(session.mode, session.session_intent),
              review: null,
              session,
              setAnswerSubmitted,
              setPhase,
              setProfileIndex,
              setReview,
              setSessionError,
              setSessionId,
              setTranscript,
              setVisiblePrompt,
              transcript: envelope.transcript,
            });
            setRestoreError("");
            setIsRestoringSession(false);
          });
          return;
        }

        if (requiresReviewRecovery(session.state)) {
          startTransition(() => {
            applySessionState({
              answerSubmitted: true,
              phase: "submitting",
              profileIndex: profileIndexFor(session.mode, session.session_intent),
              review: null,
              session,
              setAnswerSubmitted,
              setPhase,
              setProfileIndex,
              setReview,
              setSessionError,
              setSessionId,
              setTranscript,
              setVisiblePrompt,
              transcript: envelope.transcript,
            });
          });

          try {
            const restoredReview = await evaluateOrLoadReview(session.session_id);
            if (cancelled) {
              return;
            }
            startTransition(() => {
              applySessionState({
                answerSubmitted: true,
                phase: "review",
                profileIndex: profileIndexFor(session.mode, session.session_intent),
                review: restoredReview,
                session,
                setAnswerSubmitted,
                setPhase,
                setProfileIndex,
                setReview,
                setSessionError,
                setSessionId,
                setTranscript,
                setVisiblePrompt,
                transcript: envelope.transcript,
              });
              setRestoreError("");
              setIsRestoringSession(false);
            });
            return;
          } catch (error) {
            if (cancelled) {
              return;
            }
            startTransition(() => {
              applySessionState({
                answerSubmitted: true,
                phase: "session",
                profileIndex: profileIndexFor(session.mode, session.session_intent),
                review: null,
                session,
                setAnswerSubmitted,
                setPhase,
                setProfileIndex,
                setReview,
                setSessionError,
                setSessionId,
                setTranscript,
                setVisiblePrompt,
                transcript: envelope.transcript,
              });
              setSessionError(errorMessage(error));
              setIsRestoringSession(false);
            });
            return;
          }
        }

        if (session.state === "review_presented") {
          startTransition(() => {
            applySessionState({
              answerSubmitted: true,
              phase: "submitting",
              profileIndex: profileIndexFor(session.mode, session.session_intent),
              review: null,
              session,
              setAnswerSubmitted,
              setPhase,
              setProfileIndex,
              setReview,
              setSessionError,
              setSessionId,
              setTranscript,
              setVisiblePrompt,
              transcript: envelope.transcript,
            });
          });

          try {
            const restoredReview = await getReview(session.session_id);
            if (cancelled) {
              return;
            }
            startTransition(() => {
              applySessionState({
                answerSubmitted: true,
                phase: "review",
                profileIndex: profileIndexFor(session.mode, session.session_intent),
                review: restoredReview,
                session,
                setAnswerSubmitted,
                setPhase,
                setProfileIndex,
                setReview,
                setSessionError,
                setSessionId,
                setTranscript,
                setVisiblePrompt,
                transcript: envelope.transcript,
              });
              setRestoreError("");
              setIsRestoringSession(false);
            });
            return;
          } catch (error) {
            if (cancelled) {
              return;
            }
            startTransition(() => {
              applySessionState({
                answerSubmitted: true,
                phase: "session",
                profileIndex: profileIndexFor(session.mode, session.session_intent),
                review: null,
                session,
                setAnswerSubmitted,
                setPhase,
                setProfileIndex,
                setReview,
                setSessionError,
                setSessionId,
                setTranscript,
                setVisiblePrompt,
                transcript: envelope.transcript,
              });
              setSessionError(errorMessage(error));
              setIsRestoringSession(false);
            });
            return;
          }
        }

        clearSessionResumeEnvelope();
        if (cancelled) {
          return;
        }
        startTransition(() => {
          setSessionId("");
          setVisiblePrompt("");
          setTranscript("");
          setAnswerSubmitted(false);
          setSessionError("");
          setReview(null);
          setRestoreError("");
          setPhase("launcher");
          setIsRestoringSession(false);
        });
      } catch (error) {
        if (cancelled) {
          return;
        }
        if (isMissingSessionError(error)) {
          clearSessionResumeEnvelope();
        }
        startTransition(() => {
          setSessionId("");
          setVisiblePrompt("");
          setTranscript("");
          setAnswerSubmitted(false);
          setSessionError("");
          setReview(null);
          setPhase("launcher");
          setRestoreError(isMissingSessionError(error) ? "" : errorMessage(error));
          setIsRestoringSession(false);
        });
      }
    }

    void restoreSession();

    return () => {
      cancelled = true;
    };
  }, [restoreAttemptKey]);

  useEffect(() => {
    if (isRestoringSession) {
      return;
    }
    if (restoreError) {
      return;
    }
    if (!sessionId || phase === "launcher") {
      clearSessionResumeEnvelope();
      return;
    }
    writeSessionResumeEnvelope({
      sessionId,
      transcript,
      answerSubmitted,
    });
  }, [answerSubmitted, isRestoringSession, phase, restoreError, sessionId, transcript]);

  useEffect(() => {
    let cancelled = false;

    async function loadRecommendation() {
      if (!shouldLoadLauncherData) {
        return;
      }

      setIsLoadingRecommendation(true);
      setRecommendationError("");
      const storedRecommendation =
        recommendationReloadKey === 0 ? readStoredRecommendation() : null;
      if (storedRecommendation !== null) {
        startTransition(() => {
          setRecommendation(storedRecommendation);
          setIsLoadingRecommendation(false);
        });
        return;
      }
      setRecommendation(null);

      try {
        const response = await getNextRecommendation();

        if (cancelled) {
          return;
        }

        startTransition(() => {
          setRecommendation(response);
          setIsLoadingRecommendation(false);
        });
        writeStoredRecommendation(response);
      } catch (error) {
        if (cancelled) {
          return;
        }

        startTransition(() => {
          setRecommendationError(errorMessage(error));
          setIsLoadingRecommendation(false);
        });
      }
    }

    void loadRecommendation();

    return () => {
      cancelled = true;
    };
  }, [recommendationReloadKey, shouldLoadLauncherData]);

  useEffect(() => {
    let cancelled = false;

    async function loadLaunchOptions() {
      if (!shouldLoadLauncherData) {
        return;
      }

      setIsLoadingOptions(true);
      setLauncherError("");
      setLaunchOptions([]);
      setSelectedUnitId("");

      try {
        const response = await getManualLaunchOptions(
          activeProfile.mode,
          activeProfile.sessionIntent,
        );

        if (cancelled) {
          return;
        }

        startTransition(() => {
          setLaunchOptions(response.items);
          setSelectedUnitId(response.items[0]?.unit_id ?? "");
          setIsLoadingOptions(false);
        });
      } catch (error) {
        if (cancelled) {
          return;
        }

        startTransition(() => {
          setLauncherError(errorMessage(error));
          setIsLoadingOptions(false);
        });
      }
    }

    void loadLaunchOptions();

    return () => {
      cancelled = true;
    };
  }, [activeProfile.mode, activeProfile.sessionIntent, shouldLoadLauncherData]);

  useEffect(() => {
    let cancelled = false;

    async function loadLearnerSummary() {
      if (!shouldLoadLauncherData) {
        return;
      }

      setIsLoadingSummary(true);
      setSummaryError("");
      setLearnerSummary(null);

      try {
        const response = await getLearnerSummary();
        if (cancelled) {
          return;
        }
        startTransition(() => {
          setLearnerSummary(response);
          setIsLoadingSummary(false);
        });
      } catch (error) {
        if (cancelled) {
          return;
        }
        startTransition(() => {
          setSummaryError(errorMessage(error));
          setIsLoadingSummary(false);
        });
      }
    }

    void loadLearnerSummary();

    return () => {
      cancelled = true;
    };
  }, [shouldLoadLauncherData]);

  async function handleStartRecommendedSession() {
    if (!recommendation) {
      setSessionError("No recommendation is currently available.");
      return;
    }

    setIsStartingSession(true);
    setSessionError("");

    try {
      const response = await startRecommendedSession(
        recommendation.decision_id,
        recommendation.chosen_action,
      );
      clearStoredRecommendation();

      startTransition(() => {
        setProfileIndex(
          profileIndexFor(
            recommendation.chosen_action.mode,
            recommendation.chosen_action.session_intent,
          ),
        );
        setSessionId(response.session_id);
        setVisiblePrompt(response.current_unit.visible_prompt);
        setTranscript("");
        setAnswerSubmitted(false);
        setReview(null);
        setPhase("session");
        setIsStartingSession(false);
      });
    } catch (error) {
      if (isStaleRecommendationStartError(error)) {
        clearStoredRecommendation();
        setRecommendation(null);
        setRecommendationError("");
        setIsLoadingRecommendation(true);

        try {
          const freshRecommendation = await getNextRecommendation();
          writeStoredRecommendation(freshRecommendation);

          startTransition(() => {
            setRecommendation(freshRecommendation);
            setRecommendationError(
              "The saved recommendation is no longer available. Loaded a fresh recommendation.",
            );
            setSessionError("");
            setIsLoadingRecommendation(false);
            setIsStartingSession(false);
          });
          return;
        } catch (reloadError) {
          startTransition(() => {
            setRecommendation(null);
            setRecommendationError(
              "The saved recommendation is no longer available, and a fresh recommendation could not be loaded: "
                + errorMessage(reloadError),
            );
            setSessionError("");
            setIsLoadingRecommendation(false);
            setIsStartingSession(false);
          });
          return;
        }
      }

      startTransition(() => {
        setSessionError(errorMessage(error));
        setIsStartingSession(false);
      });
    }
  }

  async function handleStartSession() {
    if (!selectedUnitId) {
      setSessionError("Choose a launch option before starting the session.");
      return;
    }

    setIsStartingSession(true);
    setSessionError("");

    try {
      const response = await startManualSession(
        activeProfile.mode,
        activeProfile.sessionIntent,
        selectedUnitId,
      );
      clearStoredRecommendation();

      startTransition(() => {
        setSessionId(response.session_id);
        setVisiblePrompt(response.current_unit.visible_prompt);
        setTranscript("");
        setAnswerSubmitted(false);
        setReview(null);
        setPhase("session");
        setIsStartingSession(false);
      });
    } catch (error) {
      startTransition(() => {
        setSessionError(errorMessage(error));
        setIsStartingSession(false);
      });
    }
  }

  async function handleSubmitAnswer() {
    if (!sessionId) {
      setSessionError("Start a session before submitting an answer.");
      return;
    }
    if (!answerSubmitted && !transcript.trim()) {
      setSessionError("Write an answer before requesting review.");
      return;
    }

    setSessionError("");
    setPhase("submitting");
    let submissionAccepted = answerSubmitted;

    try {
      if (!submissionAccepted) {
        await submitAnswer(sessionId, transcript);
        submissionAccepted = true;
      }
      const evaluateResponse = await evaluateOrLoadReview(sessionId);

      startTransition(() => {
        setAnswerSubmitted(true);
        setReview(evaluateResponse);
        setPhase("review");
      });
    } catch (error) {
      startTransition(() => {
        setAnswerSubmitted(submissionAccepted);
        setSessionError(errorMessage(error));
        setPhase("session");
      });
    }
  }

  async function handleReset() {
    if (isReturningToLauncher) {
      return;
    }

    setIsReturningToLauncher(true);
    setSessionError("");

    if (sessionId) {
      try {
        await closeSessionForLauncherExit(sessionId, phase);
      } catch (error) {
        startTransition(() => {
          setSessionError(errorMessage(error));
          setIsReturningToLauncher(false);
        });
        return;
      }
    }

    clearSessionResumeEnvelope();
    clearStoredRecommendation();
    startTransition(() => {
      setPhase("launcher");
      setSessionId("");
      setVisiblePrompt("");
      setTranscript("");
      setAnswerSubmitted(false);
      setSessionError("");
      setReview(null);
      setRecommendation(null);
      setRecommendationError("");
      setLearnerSummary(null);
      setSummaryError("");
      setRestoreError("");
      setIsReturningToLauncher(false);
      setRecommendationReloadKey((value) => value + 1);
    });
  }

  function handleRetryRestore() {
    startTransition(() => {
      setRestoreError("");
      setIsRestoringSession(true);
      setRecommendation(null);
      setRecommendationError("");
      setLaunchOptions([]);
      setLauncherError("");
      setRestoreAttemptKey((value) => value + 1);
    });
  }

  function handleDiscardSavedSession() {
    clearSessionResumeEnvelope();
    startTransition(() => {
      setRestoreError("");
      setSessionId("");
      setVisiblePrompt("");
      setTranscript("");
      setAnswerSubmitted(false);
      setSessionError("");
      setReview(null);
      setPhase("launcher");
    });
  }

  return (
    <div className="app-shell">
      <div className="ambient ambient-left" />
      <div className="ambient ambient-right" />
      <main className="app-frame">
        <header className="hero">
          <p className="eyebrow">System Design Trainer</p>
          <h1>Manual reviewed loop</h1>
          <p className="hero-copy">
            A thin shell over the verified backend path: launch one bounded unit,
            answer it, attach evaluation, and inspect the review without
            inventing frontend-only runtime semantics.
          </p>
        </header>

        <section className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-label">Launch profile</p>
              <h2>{activeProfile.label}</h2>
            </div>
            {phase !== "launcher" ? (
              <button
                className="ghost-button"
                disabled={isReturningToLauncher}
                onClick={() => void handleReset()}
                type="button"
              >
                {isReturningToLauncher ? "Returning..." : "Back to launcher"}
              </button>
            ) : null}
          </div>

          {phase === "launcher" && restoreError ? (
            <div className="launcher-section">
              <p className="error-banner">{restoreError}</p>
              <button
                className="primary-button"
                onClick={handleRetryRestore}
                type="button"
              >
                Retry saved session
              </button>
              <button
                className="ghost-button"
                onClick={handleDiscardSavedSession}
                type="button"
              >
                Discard saved session
              </button>
            </div>
          ) : null}

          {phase === "launcher" && !restoreError ? (
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
                onClick={() => void handleStartRecommendedSession()}
                type="button"
              >
                {isStartingSession ? "Starting session..." : "Start recommended session"}
              </button>
            </div>
          ) : null}

          {phase === "launcher" && !restoreError ? (
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
                    <strong>{learnerSummary.readiness_summary?.title ?? "Summary unavailable"}</strong>
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
                      <p className="empty-state">
                        Nothing is strongly review-due yet.
                      </p>
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

          <div className="profile-grid" role="radiogroup" aria-label="Launch profile">
            {LAUNCH_PROFILES.map((profile, index) => {
              const checked = index === profileIndex;
              return (
                <label
                  className={`profile-card${checked ? " selected" : ""}`}
                  key={`${profile.mode}-${profile.sessionIntent}`}
                >
                  <input
                    checked={checked}
                    disabled={!isLauncherPhase}
                    name="launch-profile"
                    onChange={() => {
                      if (!isLauncherPhase) {
                        return;
                      }
                      setProfileIndex(index);
                    }}
                    type="radio"
                  />
                  <span className="profile-title">{profile.label}</span>
                  <span className="profile-description">{profile.description}</span>
                </label>
              );
            })}
          </div>

          {phase === "launcher" && !restoreError ? (
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
                  No launchable units are currently available for this mode and
                  intent combination.
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
                        onChange={() => setSelectedUnitId(option.unit_id)}
                        type="radio"
                      />
                      <div className="launch-option-copy">
                        <div className="launch-option-topline">
                          <strong>{option.display_title ?? option.topic_slug ?? option.unit_id}</strong>
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
                onClick={() => void handleStartSession()}
                type="button"
              >
                {isStartingSession ? "Starting session..." : "Start session"}
              </button>
            </div>
          ) : null}

          {phase === "session" || phase === "submitting" ? (
            <div className="session-section">
              <p className="panel-label">Prompt</p>
              <blockquote className="prompt-card">{visiblePrompt}</blockquote>
              <label className="answer-field">
                <span>Your answer</span>
                <textarea
                  disabled={answerSubmitted}
                  onChange={(event) => setTranscript(event.target.value)}
                  placeholder="Explain the concept in your own words, when to use it, and the trade-offs."
                  rows={10}
                  value={transcript}
                />
              </label>
              {sessionError ? <p className="error-banner">{sessionError}</p> : null}
              <button
                className="primary-button"
                disabled={phase === "submitting"}
                onClick={() => void handleSubmitAnswer()}
                type="button"
              >
                {phase === "submitting" ? "Submitting and evaluating..." : "Request review"}
              </button>
            </div>
          ) : null}

          {phase === "review" && review ? (
            <div className="review-section">
              <div className="review-metrics">
                <div className="metric-card">
                  <span>Weighted score</span>
                  <strong>{review.evaluation_result.weighted_score.toFixed(2)}</strong>
                </div>
                <div className="metric-card">
                  <span>Confidence</span>
                  <strong>{review.evaluation_result.overall_confidence.toFixed(2)}</strong>
                </div>
              </div>

              <div className="review-grid">
                <article className="review-card">
                  <p className="panel-label">Strengths</p>
                  <ul>
                    {review.review_report.strengths.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </article>

                <article className="review-card">
                  <p className="panel-label">Missed dimensions</p>
                  <ul>
                    {review.review_report.missed_dimensions.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </article>

                <article className="review-card">
                  <p className="panel-label">Reasoning gaps</p>
                  <ul>
                    {review.review_report.reasoning_gaps.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </article>

                <article className="review-card emphasis">
                  <p className="panel-label">Next focus</p>
                  <p>{review.review_report.recommended_next_focus}</p>
                  {review.review_report.support_dependence_note ? (
                    <p className="support-note">
                      {review.review_report.support_dependence_note}
                    </p>
                  ) : null}
                </article>
              </div>
            </div>
          ) : null}
        </section>
      </main>
    </div>
  );
}

function errorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return "Unexpected error";
}

async function evaluateOrLoadReview(sessionId: string): Promise<EvaluateResponse> {
  try {
    return await evaluateSession(sessionId);
  } catch (evaluationError) {
    try {
      return await getReview(sessionId);
    } catch {
      throw evaluationError;
    }
  }
}

async function closeSessionForLauncherExit(
  sessionId: string,
  phase: Phase,
): Promise<void> {
  if (phase === "review") {
    try {
      await completeRuntimeSession(sessionId);
      return;
    } catch (error) {
      if (isMissingSessionError(error)) {
        return;
      }
      if (!(error instanceof ApiError) || error.status !== 409) {
        throw error;
      }
    }
  } else {
    try {
      await abandonRuntimeSession(sessionId);
      return;
    } catch (error) {
      if (isMissingSessionError(error)) {
        return;
      }
      if (!(error instanceof ApiError) || error.status !== 409) {
        throw error;
      }
    }
  }

  let session: RuntimeSessionResponse;
  try {
    session = await getRuntimeSession(sessionId);
  } catch (error) {
    if (isMissingSessionError(error)) {
      return;
    }
    throw error;
  }

  if (session.state === "completed" || session.state === "abandoned") {
    return;
  }
  if (session.state === "review_presented") {
    await completeRuntimeSession(sessionId);
    return;
  }
  await abandonRuntimeSession(sessionId);
}

function applySessionState(payload: {
  answerSubmitted: boolean;
  phase: Phase;
  profileIndex: number;
  review: EvaluateResponse | null;
  session: RuntimeSessionResponse;
  setAnswerSubmitted: (value: boolean) => void;
  setPhase: (value: Phase) => void;
  setProfileIndex: (value: number) => void;
  setReview: (value: EvaluateResponse | null) => void;
  setSessionError: (value: string) => void;
  setSessionId: (value: string) => void;
  setTranscript: (value: string) => void;
  setVisiblePrompt: (value: string) => void;
  transcript: string;
}): void {
  payload.setProfileIndex(payload.profileIndex);
  payload.setSessionId(payload.session.session_id);
  payload.setVisiblePrompt(payload.session.current_unit.visible_prompt);
  payload.setTranscript(payload.transcript);
  payload.setAnswerSubmitted(payload.answerSubmitted);
  payload.setSessionError("");
  payload.setReview(payload.review);
  payload.setPhase(payload.phase);
}

function isPreAnswerState(state: string): boolean {
  return (
    state === "planned" ||
    state === "started" ||
    state === "unit_presented" ||
    state === "awaiting_answer"
  );
}

function requiresReviewRecovery(state: string): boolean {
  return state === "submitted" || state === "evaluation_pending" || state === "evaluated";
}

function isMissingSessionError(error: unknown): boolean {
  return isNotFoundError(error) || errorMessage(error).includes("unknown session_id");
}

function isStaleRecommendationStartError(error: unknown): boolean {
  return isNotFoundError(error);
}

function isNotFoundError(error: unknown): boolean {
  return error instanceof ApiError && error.status === 404;
}

function profileIndexFor(mode: string, sessionIntent: string): number {
  const index = LAUNCH_PROFILES.findIndex(
    (profile) =>
      profile.mode === mode && profile.sessionIntent === sessionIntent,
  );

  return index >= 0 ? index : 0;
}
