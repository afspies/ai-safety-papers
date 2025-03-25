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
  placeholder: string
}

export default function SimpleHTMLMarkdown({ content, className = "" }: SimpleHTMLMarkdownProps) {
  const [processedContent, setProcessedContent] = useState("")
  const [figureGroups, setFigureGroups] = useState<FigureGroup[]>([])
  const [singleFigures, setSingleFigures] = useState<ParsedFigure[]>([])

  useEffect(() => {
    if (typeof window === "undefined" || !content) return

    // Extract figures from markdown content
    const figures: ParsedFigure[] = []
    const figureRegex = /!\[(.*?)\]\((.*?)\)/g
    let match
    let modifiedContent = content

    // Find all figures in the content
    while ((match = figureRegex.exec(content)) !== null) {
      const alt = match[1]
      const src = match[2]
      const fullMatch = match[0]

      // Check if this is a subfigure (e.g., "Figure 7.a" or "Figure 7a")
      // Updated to handle both formats with or without a dot separator
      const subfigureRegex = /Figure\s+(\d+)[.]?([a-z\d])/i
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
    const groupPlaceholders: Record<string, string> = {}

    figures.forEach((figure) => {
      if (figure.baseNumber && figure.subIndex) {
        if (!groups[figure.baseNumber]) {
          groups[figure.baseNumber] = []
          // Use the first subfigure's placeholder for the group
          groupPlaceholders[figure.baseNumber] = `[SUBFIGURE_GROUP_${figure.baseNumber}]`
          
          // Replace individual placeholders with a group placeholder
          const placeholder = `[FIGURE_PLACEHOLDER_${figures.indexOf(figure)}]`
          modifiedContent = modifiedContent.replace(placeholder, groupPlaceholders[figure.baseNumber])
        } else {
          // Remove other placeholders of the same group
          const placeholder = `[FIGURE_PLACEHOLDER_${figures.indexOf(figure)}]`
          modifiedContent = modifiedContent.replace(placeholder, '')
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
      placeholder: groupPlaceholders[baseNumber]
    }))

    setFigureGroups(figGroups)
    setSingleFigures(singles)

    // Process markdown
    const processMarkdown = async () => {
      try {
        const rawHtml = await marked.parse(modifiedContent) as string
        // Sanitize HTML to prevent XSS
        const cleanHtml = DOMPurify.sanitize(rawHtml)
        setProcessedContent(cleanHtml)
      } catch (error) {
        console.error("Error parsing markdown:", error)
      }
    }
    
    processMarkdown()
  }, [content])

  // Render the content with figures
  const renderContent = () => {
    if (!processedContent) return null

    // Split by figure placeholders first
    const parts = processedContent.split(/\[FIGURE_PLACEHOLDER_(\d+)\]/)
    const result = []

    for (let i = 0; i < parts.length; i++) {
      // Add the text part
      if (parts[i]) {
        // Check for subfigure group placeholders
        const subParts = parts[i].split(/\[SUBFIGURE_GROUP_(\d+)\]/)
        if (subParts.length > 1) {
          // If there are subfigure groups
          for (let j = 0; j < subParts.length; j++) {
            if (subParts[j]) {
              result.push(<div key={`text-${i}-${j}`} dangerouslySetInnerHTML={{ __html: subParts[j] }} className="academic-text" />)
            }
            
            // Add subfigure group if there is one
            const groupNumber = subParts[j + 1]
            if (groupNumber) {
              const group = figureGroups.find(g => g.baseNumber === groupNumber)
              if (group) {
                result.push(
                  <SubfigureGroup
                    key={`group-${group.baseNumber}-inline`}
                    subfigures={group.figures.map((fig) => ({
                      src: fig.src,
                      alt: fig.alt,
                      index: fig.subIndex || "",
                    }))}
                    groupTitle={group.title}
                    className="my-6"
                  />
                )
              }
              j++ // Skip the next part which is the group number
            }
          }
        } else {
          // No subfigure groups in this part
          result.push(<div key={`text-${i}`} dangerouslySetInnerHTML={{ __html: parts[i] }} className="academic-text" />)
        }
      }

      // Add the figure if there is one
      const figureIndex = Number.parseInt(parts[i + 1])
      if (!isNaN(figureIndex)) {
        const figure = singleFigures[figureIndex] || singleFigures.find((f, idx) => idx === figureIndex)
        if (figure) {
          result.push(
            <ExpandableFigure key={`figure-${figureIndex}`} src={figure.src} alt={figure.alt} className="my-5" />,
          )
        }
        i++ // Skip the next part which is the figure index
      }
    }

    return result
  }

  return (
    <div className={`markdown-content text-base ${className}`}>
      <style jsx global>{`
        .academic-text p {
          margin-bottom: 0.75rem;
          line-height: 1.3;
          text-align: justify;
          text-justify: inter-word;
        }
        .academic-text h2 {
          font-size: 1.25rem;
          font-weight: 600;
          margin-top: 1rem;
          margin-bottom: 0.5rem;
        }
        .academic-text h3 {
          font-size: 1.125rem;
          font-weight: 600;
          margin-top: 0.75rem;
          margin-bottom: 0.5rem;
        }
        .academic-text ul, .academic-text ol {
          margin-bottom: 0.75rem;
          padding-left: 1.5rem;
        }
        .academic-text li {
          margin-bottom: 0.25rem;
        }
        .academic-text a {
          color: #2563eb;
          text-decoration: none;
        }
        .academic-text a:hover {
          text-decoration: underline;
        }
      `}</style>
      {/* Render the content with all figures inline */}
      {renderContent()}
    </div>
  )
}

