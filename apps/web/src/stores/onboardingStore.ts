import { create } from 'zustand'
import { persist } from 'zustand/middleware'

import type { OnboardingState } from '../types'

const initial: OnboardingState = {
  conferenceId: 'token2049',
  attendance: null,
  days: [],
  role: null,
  goals: [],
  topics: [],
  pace: 50,
  energy: 50,
  social: 50,
  mustHaves: [],
}

type Store = {
  state: OnboardingState
  step: number
  set: (patch: Partial<OnboardingState>) => void
  setStep: (n: number) => void
  reset: () => void
}

export const useOnboarding = create<Store>()(
  persist(
    (set) => ({
      state: initial,
      step: 0,
      set: (patch) => set((s) => ({ state: { ...s.state, ...patch } })),
      setStep: (n) => set({ step: n }),
      reset: () => set({ state: initial, step: 0 }),
    }),
    { name: 'sq-onboarding' },
  ),
)
