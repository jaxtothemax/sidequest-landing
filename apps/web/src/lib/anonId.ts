/**
 * Per-browser anonymous identifier.
 *
 * Generated on first read and persisted to localStorage as `sq-anon-id`.
 * Used as the key for /api/curate (POST) and /api/auth/claim — the backend
 * stores anonymous curations under this id until the user signs up and
 * claims them.
 *
 * Cleared by `clearAnonId()` after a successful /api/auth/claim so we don't
 * retry forever.
 */

const KEY = 'sq-anon-id'

function uuidv4(): string {
  const c = typeof globalThis.crypto !== 'undefined' ? globalThis.crypto : undefined
  // Prefer the browser's built-in if available (Chrome 92+, Safari 15.4+).
  if (c && typeof c.randomUUID === 'function') {
    return c.randomUUID()
  }
  // RFC 4122 §4.4 fallback.
  const bytes = new Uint8Array(16)
  if (c && typeof c.getRandomValues === 'function') {
    c.getRandomValues(bytes)
  } else {
    for (let i = 0; i < 16; i++) bytes[i] = Math.floor(Math.random() * 256)
  }
  bytes[6] = (bytes[6] & 0x0f) | 0x40
  bytes[8] = (bytes[8] & 0x3f) | 0x80
  const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}

export function getAnonId(): string {
  if (typeof window === 'undefined') return ''
  try {
    let id = window.localStorage.getItem(KEY)
    if (!id) {
      id = uuidv4()
      window.localStorage.setItem(KEY, id)
    }
    return id
  } catch {
    // Private mode / disabled storage — fall back to in-memory only.
    return uuidv4()
  }
}

export function peekAnonId(): string | null {
  if (typeof window === 'undefined') return null
  try {
    return window.localStorage.getItem(KEY)
  } catch {
    return null
  }
}

export function clearAnonId(): void {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.removeItem(KEY)
  } catch {
    // ignore
  }
}
