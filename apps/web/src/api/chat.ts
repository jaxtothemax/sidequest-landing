import { apiStream } from '../lib/fetcher'
import type { ChatMessage } from '../types'

export function chatStream(messages: ChatMessage[], model?: string) {
  return apiStream('/api/chat', { messages, model })
}
