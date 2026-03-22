import type { LaunchProfile } from "./launchProfiles";

export type ProfileSelectorProps = {
  profiles: readonly LaunchProfile[];
  selectedProfileIndex: number;
  isLauncherPhase: boolean;
  onProfileChange: (index: number) => void;
};

export function ProfileSelector({
  profiles,
  selectedProfileIndex,
  isLauncherPhase,
  onProfileChange,
}: ProfileSelectorProps) {
  return (
    <div className="profile-grid" role="radiogroup" aria-label="Launch profile">
      {profiles.map((profile, index) => {
        const checked = index === selectedProfileIndex;
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
                onProfileChange(index);
              }}
              type="radio"
            />
            <span className="profile-title">{profile.label}</span>
            <span className="profile-description">{profile.description}</span>
          </label>
        );
      })}
    </div>
  );
}
