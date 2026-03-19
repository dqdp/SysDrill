import { startTransition, useEffect, useState } from "react";

import {
  evaluateSession,
  getManualLaunchOptions,
  startManualSession,
  submitAnswer,
  type EvaluateResponse,
  type LaunchOption,
} from "./api";

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
  const [launchOptions, setLaunchOptions] = useState<LaunchOption[]>([]);
  const [selectedUnitId, setSelectedUnitId] = useState<string>("");
  const [launcherError, setLauncherError] = useState<string>("");
  const [phase, setPhase] = useState<Phase>("launcher");
  const [isLoadingOptions, setIsLoadingOptions] = useState(true);
  const [isStartingSession, setIsStartingSession] = useState(false);
  const [sessionId, setSessionId] = useState("");
  const [visiblePrompt, setVisiblePrompt] = useState("");
  const [transcript, setTranscript] = useState("");
  const [sessionError, setSessionError] = useState("");
  const [review, setReview] = useState<EvaluateResponse | null>(null);

  const activeProfile = LAUNCH_PROFILES[profileIndex] ?? LAUNCH_PROFILES[0];
  const isLauncherPhase = phase === "launcher";

  useEffect(() => {
    let cancelled = false;

    async function loadLaunchOptions() {
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
  }, [activeProfile.mode, activeProfile.sessionIntent]);

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

      startTransition(() => {
        setSessionId(response.session_id);
        setVisiblePrompt(response.current_unit.visible_prompt);
        setTranscript("");
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
    if (!transcript.trim()) {
      setSessionError("Write an answer before requesting review.");
      return;
    }

    setSessionError("");
    setPhase("submitting");

    try {
      await submitAnswer(sessionId, transcript);
      const evaluateResponse = await evaluateSession(sessionId);

      startTransition(() => {
        setReview(evaluateResponse);
        setPhase("review");
      });
    } catch (error) {
      startTransition(() => {
        setSessionError(errorMessage(error));
        setPhase("session");
      });
    }
  }

  function handleReset() {
    startTransition(() => {
      setPhase("launcher");
      setSessionId("");
      setVisiblePrompt("");
      setTranscript("");
      setSessionError("");
      setReview(null);
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
              <button className="ghost-button" onClick={handleReset} type="button">
                Back to launcher
              </button>
            ) : null}
          </div>

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

          {phase === "launcher" ? (
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
