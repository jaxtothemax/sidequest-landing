import jsPDF from 'jspdf'

import type { SeedEvent } from '../data/seedEvents'

export type SchedulePdfInput = {
  conferenceName: string
  conferenceMeta?: string | null // e.g. "29 Apr – 30 Apr · Madinat Jumeirah"
  events: SeedEvent[] // already filtered to the user's schedule, sorted by day+start
}

const PAGE_MARGIN_X = 48
const PAGE_MARGIN_TOP = 56
const PAGE_MARGIN_BOTTOM = 56
const PAGE_WIDTH = 595 // a4 portrait pt
const PAGE_HEIGHT = 842
const CONTENT_WIDTH = PAGE_WIDTH - PAGE_MARGIN_X * 2

const SQ_RED: [number, number, number] = [230, 44, 90]
const TEXT: [number, number, number] = [25, 28, 33]
const MUTED: [number, number, number] = [105, 112, 122]
const RULE: [number, number, number] = [225, 228, 232]

function fmtDayHeading(firstStart: string, day: number): string {
  const d = new Date(firstStart)
  if (Number.isNaN(d.getTime())) return `Day ${day}`
  return d.toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })
}

function fmtTimeRange(start: string, end: string): string {
  // Times come from the catalog as either "9:00 AM" (legacy seed) or already
  // formatted by useEvents (also "9:00 AM" via toLocaleTimeString). Use as-is.
  return `${start} – ${end}`
}

/**
 * Generates a PDF blob of the user's schedule and triggers a download.
 * Returns the filename used so callers can surface it in UI if desired.
 */
export function exportSchedulePdf(input: SchedulePdfInput): string {
  const doc = new jsPDF({ unit: 'pt', format: 'a4' })

  let y = PAGE_MARGIN_TOP

  const ensureSpace = (h: number) => {
    if (y + h > PAGE_HEIGHT - PAGE_MARGIN_BOTTOM) {
      doc.addPage()
      y = PAGE_MARGIN_TOP
    }
  }

  const writeWrapped = (
    text: string,
    opts: {
      x?: number
      maxWidth?: number
      size?: number
      color?: [number, number, number]
      style?: 'normal' | 'bold'
      lineHeight?: number
    } = {},
  ) => {
    const x = opts.x ?? PAGE_MARGIN_X
    const maxWidth = opts.maxWidth ?? CONTENT_WIDTH
    const size = opts.size ?? 11
    const color = opts.color ?? TEXT
    const style = opts.style ?? 'normal'
    const lineHeight = opts.lineHeight ?? size * 1.35
    doc.setFont('helvetica', style)
    doc.setFontSize(size)
    doc.setTextColor(color[0], color[1], color[2])
    const lines = doc.splitTextToSize(text, maxWidth) as string[]
    for (const line of lines) {
      ensureSpace(lineHeight)
      doc.text(line, x, y)
      y += lineHeight
    }
  }

  // ---------- Header ----------
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(22)
  doc.setTextColor(...SQ_RED)
  doc.text('SideQuest', PAGE_MARGIN_X, y)
  y += 26

  doc.setFont('helvetica', 'bold')
  doc.setFontSize(16)
  doc.setTextColor(...TEXT)
  doc.text(input.conferenceName, PAGE_MARGIN_X, y)
  y += 18

  if (input.conferenceMeta) {
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(11)
    doc.setTextColor(...MUTED)
    doc.text(input.conferenceMeta, PAGE_MARGIN_X, y)
    y += 16
  }

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(9)
  doc.setTextColor(...MUTED)
  const generated = `Your personalised schedule · Generated ${new Date().toLocaleString()}`
  doc.text(generated, PAGE_MARGIN_X, y)
  y += 22

  // Rule
  doc.setDrawColor(...RULE)
  doc.setLineWidth(0.6)
  doc.line(PAGE_MARGIN_X, y, PAGE_WIDTH - PAGE_MARGIN_X, y)
  y += 18

  // ---------- Body ----------
  if (input.events.length === 0) {
    writeWrapped('No events in your schedule yet.', { color: MUTED, size: 12 })
  } else {
    const grouped = new Map<number, SeedEvent[]>()
    for (const e of input.events) {
      const arr = grouped.get(e.day) ?? []
      arr.push(e)
      grouped.set(e.day, arr)
    }
    const days = Array.from(grouped.keys()).sort((a, b) => a - b)

    for (const day of days) {
      const items = grouped.get(day)!
      ensureSpace(40)

      // Day heading
      doc.setFont('helvetica', 'bold')
      doc.setFontSize(13)
      doc.setTextColor(...SQ_RED)
      doc.text(fmtDayHeading(items[0].start, day), PAGE_MARGIN_X, y)
      y += 6

      // Subtle underline
      doc.setDrawColor(...SQ_RED)
      doc.setLineWidth(1.2)
      doc.line(PAGE_MARGIN_X, y, PAGE_MARGIN_X + 36, y)
      y += 14

      for (const e of items) {
        ensureSpace(60)
        const blockStart = y

        // Time column (left, 110pt wide)
        doc.setFont('helvetica', 'bold')
        doc.setFontSize(10)
        doc.setTextColor(...TEXT)
        doc.text(fmtTimeRange(e.start, e.end), PAGE_MARGIN_X, y + 11)

        // Tag pill below time
        doc.setFont('helvetica', 'normal')
        doc.setFontSize(8)
        doc.setTextColor(...MUTED)
        doc.text(e.tag.toUpperCase(), PAGE_MARGIN_X, y + 25)

        // Title + venue + desc on the right column
        const rightX = PAGE_MARGIN_X + 110
        const rightW = CONTENT_WIDTH - 110

        doc.setFont('helvetica', 'bold')
        doc.setFontSize(12)
        doc.setTextColor(...TEXT)
        const titleLines = doc.splitTextToSize(e.title, rightW) as string[]
        let lineY = y + 12
        for (const line of titleLines) {
          ensureSpace(16)
          doc.text(line, rightX, lineY)
          lineY += 15
        }

        doc.setFont('helvetica', 'normal')
        doc.setFontSize(9)
        doc.setTextColor(...MUTED)
        if (e.venue) {
          doc.text(`@ ${e.venue}`, rightX, lineY)
          lineY += 13
        }

        if (e.desc) {
          doc.setFont('helvetica', 'normal')
          doc.setFontSize(10)
          doc.setTextColor(...TEXT)
          const descLines = doc.splitTextToSize(e.desc, rightW) as string[]
          for (const dl of descLines) {
            ensureSpace(14)
            doc.text(dl, rightX, lineY)
            lineY += 13
          }
        }

        const blockEnd = Math.max(lineY, blockStart + 40)
        y = blockEnd + 8

        // Inter-event divider
        doc.setDrawColor(...RULE)
        doc.setLineWidth(0.4)
        doc.line(PAGE_MARGIN_X, y, PAGE_WIDTH - PAGE_MARGIN_X, y)
        y += 10
      }

      y += 6
    }
  }

  // ---------- Footer (every page) ----------
  const totalPages = doc.getNumberOfPages()
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i)
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(8)
    doc.setTextColor(...MUTED)
    doc.text(
      `sidequest.app · page ${i} of ${totalPages}`,
      PAGE_WIDTH / 2,
      PAGE_HEIGHT - 24,
      { align: 'center' },
    )
  }

  const safeName = input.conferenceName.replace(/[^a-z0-9]+/gi, '-').toLowerCase()
  const filename = `sidequest-${safeName || 'schedule'}.pdf`
  doc.save(filename)
  return filename
}
