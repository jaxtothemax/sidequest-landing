import { create } from 'zustand'
import { persist } from 'zustand/middleware'

import type { CuratedItem, OnboardingState } from '../types'

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
  // Cached curate result so Paywall + Schedule preview can render LLM picks
  // before the user signs up + claims. Cleared on reset() or successful claim.
  curatedSchedule: CuratedItem[] | null
  curateId: string | null
  set: (patch: Partial<OnboardingState>) => void
  setStep: (n: number) => void
  setCurated: (curateId: string, schedule: CuratedItem[]) => void
  reset: () => void
}

export const useOnboarding = create<Store>()(
  persist(
    (set) => ({
      state: initial,
      step: 0,
      curatedSchedule: null,
      curateId: null,
      set: (patch) => set((s) => ({ state: { ...s.state, ...patch } })),
      setStep: (n) => set({ step: n }),
      setCurated: (curateId, schedule) => set({ curateId, curatedSchedule: schedule }),
      reset: () =>
        set({ state: initial, step: 0, curatedSchedule: null, curateId: null }),
    }),
    { name: 'sq-onboarding' },
  ),
)
