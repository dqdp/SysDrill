import { LauncherShell } from "./LauncherShell";
import { ProfileSelector } from "./ProfileSelector";
import { ReviewShell } from "./ReviewShell";
import { SessionShell } from "./SessionShell";
import { useRuntimeShell } from "./useRuntimeShell";

export function App() {
  const {
    activeProfile,
    phase,
    isReturningToLauncher,
    handleReset,
    profileSelectorProps,
    launcherProps,
    sessionProps,
    review,
  } = useRuntimeShell();

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

          <ProfileSelector {...profileSelectorProps} />

          {phase === "launcher" ? <LauncherShell {...launcherProps} /> : null}

          {phase === "session" || phase === "submitting" ? (
            <SessionShell {...sessionProps} />
          ) : null}

          {phase === "review" && review ? <ReviewShell review={review} /> : null}
        </section>
      </main>
    </div>
  );
}
