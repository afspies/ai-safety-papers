"use client"

import { useEffect, useState } from "react"
import DOMPurify from "dompurify"
import { marked } from "marked"
import ExpandableFigure from "./expandable-figure"
import SubfigureGroup from "./subfigure-group"

interface SimpleHTMLMarkdownProps {
  content: string
  className?: string
}

interface ParsedFigure {
  src: string
  alt: string
  baseNumber?: string
  subIndex?: string
  fullMatch: string
}

interface FigureGroup {
  baseNumber: string
  title: string
  figures: ParsedFigure[]
}

export default function SimpleHTMLMarkdown({ content, className = "" }: SimpleHTMLMarkdownProps) {
  const [processedContent, setProcessedContent] = useState("")
  const [figureGroups, setFigureGroups] = useState<FigureGroup[]>([])
  const [singleFigures, setSingleFigures] = useState<ParsedFigure[]>([])

  useEffect(() => {
    if (typeof window === "undefined" || !content) return

    // Extract figures from markdown content
    const figures: ParsedFigure[] = []
    const figureRegex = /!\[(.*?)\]$$(.*?)$$/g
    let match
    let modifiedContent = content

    // Find all figures in the content
    while ((match = figureRegex.exec(content)) !== null) {
      const alt = match[1]
      const src = match[2]
      const fullMatch = match[0]

      // Check if this is a subfigure (e.g., "Figure 7.a")
      const subfigureRegex = /Figure\s+(\d+)\.([a-z])/i
      const subfigureMatch = alt.match(subfigureRegex)

      if (subfigureMatch) {
        figures.push({
          src,
          alt,
          baseNumber: subfigureMatch[1],
          subIndex: subfigureMatch[2],
          fullMatch,
        })
      } else {
        figures.push({
          src,
          alt,
          fullMatch,
        })
      }

      // Remove the figure from the content - we'll render it separately
      modifiedContent = modifiedContent.replace(fullMatch, `[FIGURE_PLACEHOLDER_${figures.length - 1}]`)
    }

    // Group subfigures
    const groups: Record<string, ParsedFigure[]> = {}
    const singles: ParsedFigure[] = []

    figures.forEach((figure) => {
      if (figure.baseNumber && figure.subIndex) {
        if (!groups[figure.baseNumber]) {
          groups[figure.baseNumber] = []
        }
        groups[figure.baseNumber].push(figure)
      } else {
        singles.push(figure)
      }
    })

    // Create figure groups
    const figGroups: FigureGroup[] = Object.keys(groups).map((baseNumber) => ({
      baseNumber,
      title: `Figure ${baseNumber}`,
      figures: groups[baseNumber].sort((a, b) => (a.subIndex || "").localeCompare(b.subIndex || "")),
    }))

    setFigureGroups(figGroups)
    setSingleFigures(singles)

    // Convert markdown to HTML (excluding figures)
    const rawHtml = marked.parse(modifiedContent)

    // Sanitize HTML to prevent XSS
    const cleanHtml = DOMPurify.sanitize(rawHtml)
    setProcessedContent(cleanHtml)
  }, [content])

  // Render the content with figures
  const renderContent = () => {
    if (!processedContent) return null

    // Split by figure placeholders
    const parts = processedContent.split(/\[FIGURE_PLACEHOLDER_(\d+)\]/)
    const result = []

    for (let i = 0; i < parts.length; i++) {
      // Add the text part
      if (parts[i]) {
        result.push(<div key={`text-${i}`} dangerouslySetInnerHTML={{ __html: parts[i] }} />)
      }

      // Add the figure if there is one
      const figureIndex = Number.parseInt(parts[i + 1])
      if (!isNaN(figureIndex)) {
        const figure = [...singleFigures, ...figureGroups.flatMap((g) => g.figures)][figureIndex]
        if (figure) {
          result.push(
            <ExpandableFigure key={`figure-${figureIndex}`} src={figure.src} alt={figure.alt} className="my-6" />,
          )
        }
        i++ // Skip the next part which is the figure index
      }
    }

    return result
  }

  return (
    <div className={`markdown-content ${className}`}>
      {/* Render subfigure groups at the top */}
      {figureGroups.map((group) => (
        <SubfigureGroup
          key={`group-${group.baseNumber}`}
          subfigures={group.figures.map((fig) => ({
            src: fig.src,
            alt: fig.alt,
            index: fig.subIndex || "",
          }))}
          groupTitle={group.title}
          className="mb-8"
        />
      ))}

      {/* Render the main content with single figures inline */}
      {renderContent()}
    </div>
  )
}

