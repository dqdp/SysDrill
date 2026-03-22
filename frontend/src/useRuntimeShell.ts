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
import { LAUNCH_PROFILES, profileIndexFor } from "./launchProfiles";
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

export type Phase = "launcher" | "session" | "submitting" | "review";

export function useRuntimeShell() {
  const [profileIndex, setProfileIndex] = useState(0);
  const [recommendation, setRecommendation] =
    useState<RecommendationDecisionResponse | null>(null);
  const [recommendationError, setRecommendationError] = useState("");
  const [isLoadingRecommendation, setIsLoadingRecommendation] = useState(true);
  const [recommendationReloadKey, setRecommendationReloadKey] = useState(0);
  const [restoreAttemptKey, setRestoreAttemptKey] = useState(0);
  const [restoreError, setRestoreError] = useState("");
  const [learnerSummary, setLearnerSummary] =
    useState<LearnerSummaryResponse | null>(null);
  const [summaryError, setSummaryError] = useState("");
  const [launchOptions, setLaunchOptions] = useState<LaunchOption[]>([]);
  const [selectedUnitId, setSelectedUnitId] = useState("");
  const [launcherError, setLauncherError] = useState("");
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
  const sessionPhase: "session" | "submitting" =
    phase === "submitting" ? "submitting" : "session";
  const shouldLoadLauncherData = isLauncherPhase && !isRestoringSession && !restoreError;

  // Restore is the only place that reconstructs UI state from browser-local
  // scaffolding, so its ordering must stay aligned with backend session states.
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

      if (!isPreAnswerState(response.state)) {
        writeSessionResumeEnvelope({
          sessionId: response.session_id,
          transcript: "",
          answerSubmitted: response.state !== "awaiting_answer",
        });
        startTransition(() => {
          setSessionError("");
          setRestoreError("");
          setIsRestoringSession(true);
          setRecommendation(null);
          setRecommendationError("");
          setLaunchOptions([]);
          setLauncherError("");
          setIsStartingSession(false);
          setRestoreAttemptKey((value) => value + 1);
        });
        return;
      }

      startTransition(() => {
        setProfileIndex(
          profileIndexFor(
            response.mode ?? recommendation.chosen_action.mode,
            response.session_intent ?? recommendation.chosen_action.session_intent,
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
    let finalSubmissionAccepted = answerSubmitted;

    try {
      if (!answerSubmitted) {
        const submissionResponse = await submitAnswer(sessionId, transcript);
        if (submissionResponse.state === "follow_up_round") {
          const nextPrompt = submissionResponse.current_unit?.visible_prompt;
          if (!nextPrompt) {
            throw new Error("Follow-up round started without a visible prompt.");
          }
          startTransition(() => {
            setAnswerSubmitted(false);
            setVisiblePrompt(nextPrompt);
            setTranscript("");
            setPhase("session");
          });
          return;
        }
        if (submissionResponse.state !== "evaluation_pending") {
          throw new Error(
            `Unsupported session state after submission: ${submissionResponse.state}`,
          );
        }
        finalSubmissionAccepted = true;
      }

      const evaluateResponse = await evaluateOrLoadReview(sessionId);

      startTransition(() => {
        setAnswerSubmitted(true);
        setReview(evaluateResponse);
        setPhase("review");
      });
    } catch (error) {
      startTransition(() => {
        setAnswerSubmitted(finalSubmissionAccepted);
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

  return {
    activeProfile,
    phase,
    isReturningToLauncher,
    handleReset,
    profileSelectorProps: {
      profiles: LAUNCH_PROFILES,
      selectedProfileIndex: profileIndex,
      isLauncherPhase,
      onProfileChange: setProfileIndex,
    },
    launcherProps: {
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
      onStartRecommendedSession: () => {
        void handleStartRecommendedSession();
      },
      onSelectUnit: setSelectedUnitId,
      onStartSession: () => {
        void handleStartSession();
      },
      onRetryRestore: handleRetryRestore,
      onDiscardSavedSession: handleDiscardSavedSession,
    },
    sessionProps: {
      answerSubmitted,
      onSubmitAnswer: () => {
        void handleSubmitAnswer();
      },
      onTranscriptChange: setTranscript,
      phase: sessionPhase,
      sessionError,
      transcript,
      visiblePrompt,
    },
    review,
  };
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
    state === "awaiting_answer" ||
    state === "follow_up_round"
  );
}

function requiresReviewRecovery(state: string): boolean {
  return state === "submitted" || state === "evaluation_pending" || state === "evaluated";
}

function isMissingSessionError(error: unknown): boolean {
  return isNotFoundError(error) || errorMessage(error).includes("unknown session_id");
}

function isStaleRecommendationStartError(error: unknown): boolean {
  if (isNotFoundError(error)) {
    return true;
  }
  if (!(error instanceof ApiError) || error.status !== 400) {
    return false;
  }

  const message = errorMessage(error);
  return [
    "unknown decision_id",
    "request action does not match stored chosen_action",
    "is not currently resolvable",
    "does not match resolved unit",
    "unsupported runtime mode/session_intent combination",
  ].some((detail) => message.includes(detail));
}

function isNotFoundError(error: unknown): boolean {
  return error instanceof ApiError && error.status === 404;
}
