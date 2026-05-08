import { supabase } from './supabase'

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? ''

async function authHeader(): Promise<HeadersInit> {
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  for (const [k, v] of Object.entries(await authHeader())) headers.set(k, v as string)
  if (init.body && !headers.has('content-type')) headers.set('content-type', 'application/json')

  const r = await fetch(`${BASE}${path}`, { ...init, headers })
  if (!r.ok) {
    const text = await r.text().catch(() => '')
    throw new Error(`${r.status} ${r.statusText}: ${text}`)
  }
  return r.json() as Promise<T>
}

/** Returns a ReadableStream of decoded SSE frames. Each frame is one JSON object. */
export async function apiStream(
  path: string,
  body: unknown,
): Promise<ReadableStream<{ type: string; content?: string }>> {
  const headers = new Headers({ 'content-type': 'application/json', accept: 'text/event-stream' })
  for (const [k, v] of Object.entries(await authHeader())) headers.set(k, v as string)

  const r = await fetch(`${BASE}${path}`, { method: 'POST', headers, body: JSON.stringify(body) })
  if (!r.ok || !r.body) throw new Error(`${r.status} ${r.statusText}`)

  const decoder = new TextDecoder()
  let buf = ''
  return new ReadableStream({
    async start(controller) {
      const reader = r.body!.getReader()
      try {
        while (true) {
          const { value, done } = await reader.read()
          if (done) break
          buf += decoder.decode(value, { stream: true })
          // SSE frames are separated by a blank line.
          const parts = buf.split('\n\n')
          buf = parts.pop() ?? ''
          for (const part of parts) {
            const dataLine = part.split('\n').find((l) => l.startsWith('data: '))
            if (!dataLine) continue
            const payload = dataLine.slice(6)
            if (payload === '[DONE]') {
              controller.close()
              return
            }
            try {
              controller.enqueue(JSON.parse(payload))
            } catch {
              // ignore malformed frame
            }
          }
        }
        controller.close()
      } catch (err) {
        controller.error(err)
      }
    },
  })
}
