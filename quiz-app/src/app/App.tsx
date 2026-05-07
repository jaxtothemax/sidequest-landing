import { useState } from "react";
import Onboarding, { type State as OnboardingState } from "./components/Onboarding";
import MainApp from "./components/MainApp";
import Paywall from "./components/Paywall";

export default function App() {
  const [completed, setCompleted] = useState<OnboardingState | null>(null);
  const [unlocked, setUnlocked] = useState(false);

  if (completed && unlocked) {
    return (
      <MainApp
        state={completed}
        onLogout={() => {
          setCompleted(null);
          setUnlocked(false);
        }}
      />
    );
  }
  if (completed) {
    return <Paywall onUnlock={() => setUnlocked(true)} />;
  }
  return <Onboarding onComplete={(s) => setCompleted(s)} />;
}
