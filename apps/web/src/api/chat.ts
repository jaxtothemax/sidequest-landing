import { apiStream } from '../lib/fetcher'
import type { ChatMessage } from '../types'

export function chatStream(
  messages: ChatMessage[],
  opts: { model?: string; conferenceId?: string } = {},
) {
  return apiStream('/api/chat', {
    messages,
    model: opts.model,
    conference_id: opts.conferenceId,
  })
}
