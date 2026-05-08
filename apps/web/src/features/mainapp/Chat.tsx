import { useEffect, useRef, useState } from 'react'
import { Send } from 'lucide-react'

import SymbolSVG from '../../assets/Symbol.svg'
import { chatStream } from '../../api/chat'
import { useEvents } from '../../hooks/useEvents'
import type { ChatMessage } from '../../types'

type ChatMsg = ChatMessage & { id: string; chips?: string[] }

const INITIAL: ChatMsg[] = [
  {
    id: 'm1',
    role: 'assistant',
    content:
      "Welcome! I've curated events across your days based on your goals. Want me to walk you through Wednesday, swap anything, or just ask me about logistics?",
    chips: ['Walk me through Wed', 'Swap an event', 'Dress code?', 'Best route between venues'],
  },
]

export function ChatPage() {
  const { events } = useEvents()
  const [messages, setMessages] = useState<ChatMsg[]>(INITIAL)
  const [input, setInput] = useState('')
  const [thinking, setThinking] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, thinking])

  const send = async (text: string) => {
    const trimmed = text.trim()
    if (!trimmed) return
    const userMsg: ChatMsg = { id: `u${Date.now()}`, role: 'user', content: trimmed }
    const next = [...messages, userMsg]
    setMessages(next)
    setInput('')
    setThinking(true)

    const replyId = `a${Date.now()}`
    const placeholder: ChatMsg = { id: replyId, role: 'assistant', content: '' }
    setMessages((m) => [...m, placeholder])

    try {
      const stream = await chatStream(
        next.map((m) => ({ role: m.role, content: m.content })),
      )
      const reader = stream.getReader()
      let acc = ''
      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        if (value?.type === 'delta' && value.content) {
          acc += value.content
          setMessages((m) =>
            m.map((mm) => (mm.id === replyId ? { ...mm, content: acc } : mm)),
          )
        }
      }
      if (!acc.trim()) {
        // Fallback when API isn't reachable yet — keep the UX testable.
        setMessages((m) =>
          m.map((mm) =>
            mm.id === replyId
              ? {
                  ...mm,
                  content:
                    "I couldn't reach the assistant. Make sure the backend is running and you're signed in.",
                }
              : mm,
          ),
        )
      }
    } catch (err) {
      setMessages((m) =>
        m.map((mm) =>
          mm.id === replyId ? { ...mm, content: `Error: ${(err as Error).message}` } : mm,
        ),
      )
    } finally {
      setThinking(false)
    }
  }

  const scheduledCount = events.filter((e) => e.inSchedule).length

  return (
    <div className="chat">
      <div className="chat__header">
        <div className="chat__avatar">
          <img src={SymbolSVG} alt="" />
        </div>
        <div className="chat__title-wrap">
          <div className="chat__title">SideQuest Agent</div>
          <div className="chat__sub">
            <span className="chat__dot" /> {scheduledCount} events on your plan
          </div>
        </div>
      </div>

      <div ref={scrollRef} className="chat__scroll">
        {messages.map((m) => (
          <div key={m.id} className={`chat-msg chat-msg--${m.role === 'user' ? 'user' : 'agent'}`}>
            {m.role === 'assistant' && (
              <div className="chat-msg__avatar">
                <img src={SymbolSVG} alt="" />
              </div>
            )}
            <div className="chat-msg__bubble">
              <div className="chat-msg__text">{m.content}</div>
              {m.chips && (
                <div className="chat-msg__chips">
                  {m.chips.map((c) => (
                    <button key={c} className="chat-chip" onClick={() => send(c)}>
                      {c}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {thinking && (
          <div className="chat-msg chat-msg--agent">
            <div className="chat-msg__avatar">
              <img src={SymbolSVG} alt="" />
            </div>
            <div className="chat-msg__bubble">
              <div className="chat-typing">
                <span />
                <span />
                <span />
              </div>
            </div>
          </div>
        )}
      </div>

      <form
        className="chat__input"
        onSubmit={(e) => {
          e.preventDefault()
          void send(input)
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your schedule, dress code, directions…"
        />
        <button type="submit" className="chat__send" disabled={!input.trim()} aria-label="Send">
          <Send size={18} />
        </button>
      </form>
    </div>
  )
}
