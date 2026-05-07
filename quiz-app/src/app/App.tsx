import { useState } from "react";
import Onboarding, { type State as OnboardingState } from "./components/Onboarding";
import MainApp from "./components/MainApp";

export default function App() {
  const [completed, setCompleted] = useState<OnboardingState | null>(null);
  if (completed) return <MainApp state={completed} onLogout={() => setCompleted(null)} />;
  return <Onboarding onComplete={(s) => setCompleted(s)} />;
}
