"use client"

import { useEffect, useState } from "react"
import DOMPurify from "dompurify"
import { marked } from "marked"
import ExpandableFigure from "./expandable-figure"
import SubfigureGroup from "./subfigure-group"
import { FigureSchema } from "@/lib/types"

interface SimpleHTMLMarkdownProps {
  content: string
  className?: string
  figures?: FigureSchema[]
}

interface ParsedFigure {
  src: string
  alt: string
  baseNumber?: string
  subIndex?: string
  fullMatch: string
  caption?: string
  parent_caption?: string
}

interface FigureGroup {
  baseNumber: string
  title: string
  figures: ParsedFigure[]
  placeholder: string
  caption?: string
}

export default function SimpleHTMLMarkdown({ content, className = "", figures = [] }: SimpleHTMLMarkdownProps) {
  const [processedContent, setProcessedContent] = useState("")
  const [figureGroups, setFigureGroups] = useState<FigureGroup[]>([])
  const [singleFigures, setSingleFigures] = useState<ParsedFigure[]>([])
  const [parsedFigures, setParsedFigures] = useState<ParsedFigure[]>([])

  useEffect(() => {
    if (typeof window === "undefined" || !content) return

    // Extract figures from markdown content
    const parsedFigures: ParsedFigure[] = []
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
        parsedFigures.push({
          src,
          alt,
          baseNumber: subfigureMatch[1],
          subIndex: subfigureMatch[2],
          fullMatch,
        })
      } else {
        // Check for regular figure pattern like "Figure 3"
        const figureRegex = /Figure\s+(\d+)/i
        const figureMatch = alt.match(figureRegex)
        const figureNumber = figureMatch ? figureMatch[1] : undefined

        parsedFigures.push({
          src,
          alt,
          baseNumber: figureNumber,
          fullMatch,
        })
      }

      // Important: Keep track of the original position of each figure in the content
      // Replace with a unique placeholder that preserves the exact position
      modifiedContent = modifiedContent.replace(fullMatch, `[FIGURE_PLACEHOLDER_${parsedFigures.length - 1}]`)
    }

    // Match captions from API figures
    if (figures && figures.length > 0) {
      // Debug the API figures data structure
      console.log("API Figures:", figures.map(f => ({ 
        id: f.id, 
        hasSubfigures: f.has_subfigures,
        hasParentCaption: !!f.parent_caption,
        captionLength: f.caption ? f.caption.length : 0
      })));

      // First organize API figures by ID for easy lookup
      const apiSubfigures: Record<string, FigureSchema> = {};
      
      // Look for figures with IDs like "2.a" or "2a" which are subfigures
      figures.forEach(figure => {
        if (figure.id) {
          apiSubfigures[figure.id] = figure;
        }
      });
      
      parsedFigures.forEach((figure, index) => {
        if (figure.baseNumber) {
          // For subfigures, check if we have an exact match in the API data
          if (figure.subIndex) {
            // Check for different subfigure ID formats (e.g., "2.a" or "2a")
            const possibleSubfigureIds = [
              `${figure.baseNumber}.${figure.subIndex}`.toLowerCase(),
              `${figure.baseNumber}${figure.subIndex}`.toLowerCase()
            ];
            
            // Look for matching subfigure in API data
            let matchingSubfigure: FigureSchema | undefined;
            for (const id of possibleSubfigureIds) {
              if (apiSubfigures[id]) {
                matchingSubfigure = apiSubfigures[id];
                break;
              }
              const normalizedId = id.toLowerCase(); // Try case insensitive match
              const matchKey = Object.keys(apiSubfigures).find(key => key.toLowerCase() === normalizedId);
              if (matchKey) {
                matchingSubfigure = apiSubfigures[matchKey];
                break;
              }
            }
            
            if (matchingSubfigure) {
              console.log(`Found matching subfigure for ${figure.baseNumber}.${figure.subIndex}:`, matchingSubfigure);
              
              // If the subfigure has parent_caption, use it
              if (matchingSubfigure.parent_caption) {
                figure.parent_caption = matchingSubfigure.parent_caption;
                console.log(`Setting parent_caption for ${figure.baseNumber}.${figure.subIndex}:`, figure.parent_caption);
              }
              
              // If the subfigure has its own caption, use it
              if (matchingSubfigure.caption) {
                figure.caption = matchingSubfigure.caption;
              }
            } else {
              // Try to find the parent figure and use its caption as parent_caption
              const parentFigure = figures.find(f => f.id === figure.baseNumber);
              if (parentFigure && parentFigure.caption) {
                figure.parent_caption = parentFigure.caption;
                console.log(`Using parent figure caption for ${figure.baseNumber}.${figure.subIndex}:`, figure.parent_caption);
              }
            }
          } else {
            // Regular figure, try to find a match in API data
            const matchingAPIFigure = figures.find(f => f.id === figure.baseNumber);
            if (matchingAPIFigure && matchingAPIFigure.caption) {
              figure.caption = matchingAPIFigure.caption;
            }
          }
        }
      });
    }

    // Group subfigures by their base number for reference
    const groups: Record<string, ParsedFigure[]> = {}
    const singles: ParsedFigure[] = []
    const groupPlaceholders: Record<string, string> = {}
    const groupCaptions: Record<string, string> = {}

    // First pass - identify subfigures and create groups
    parsedFigures.forEach((figure) => {
      if (figure.baseNumber && figure.subIndex) {
        if (!groups[figure.baseNumber]) {
          groups[figure.baseNumber] = []
          
          // Set caption for the group from API data
          if (figures && figures.length > 0) {
            const matchingAPIFigure = figures.find(f => f.id === figure.baseNumber)
            if (matchingAPIFigure && matchingAPIFigure.caption) {
              groupCaptions[figure.baseNumber] = matchingAPIFigure.caption
            }
          }
        }
        groups[figure.baseNumber].push(figure)
      } else {
        singles.push(figure)
      }
    })

    // Mark each figure's placement and organize groups
    // But we keep every figure in its original position
    parsedFigures.forEach((figure, index) => {
      const placeholder = `[FIGURE_PLACEHOLDER_${index}]`;
      
      if (figure.baseNumber && figure.subIndex) {
        const groupKey = figure.baseNumber;
        
        // Register this placeholder, but don't remove any figures
        if (!groupPlaceholders[groupKey]) {
          groupPlaceholders[groupKey] = placeholder;
        }
      }
    });

    // Create figure groups for reference when rendering
    const figGroups: FigureGroup[] = []
    
    Object.keys(groups).forEach((baseNumber) => {
      const groupFigures = groups[baseNumber]
      
      // Only create groups if there are multiple subfigures
      if (groupFigures.length > 1) {
        figGroups.push({
          baseNumber,
          title: `Figure ${baseNumber}`,
          figures: groupFigures.sort((a, b) => (a.subIndex || "").localeCompare(b.subIndex || "")),
          placeholder: groupPlaceholders[baseNumber],
          caption: groupCaptions[baseNumber]
        })

        // Update subfigures within the group to have the parent caption
        groupFigures.forEach(fig => {
          fig.caption = fig.caption || undefined; // Ensure individual captions exist if set
        });
      }
    })

    // After creating all the groups, set their captions and make sure subfigures have parent_caption
    figGroups.forEach(group => {
      // Find all subfigures with parent_caption
      const subfiguresWithParentCaption = group.figures.filter(fig => fig.parent_caption);
      
      // If any subfigure has parent_caption, use that for the group caption
      if (subfiguresWithParentCaption.length > 0) {
        group.caption = subfiguresWithParentCaption[0].parent_caption;
        
        // Ensure all subfigures have the parent_caption set
        group.figures.forEach(fig => {
          if (!fig.parent_caption) {
            fig.parent_caption = group.caption;
          }
        });
      }
    });

    // Debug logs for figure groups and their parent_captions
    console.log("Figure Groups with captions:", figGroups.map(g => ({
      baseNumber: g.baseNumber,
      caption: g.caption,
      subFiguresWithParentCaption: g.figures.filter(f => f.parent_caption).length,
      totalSubfigures: g.figures.length
    })));

    setFigureGroups(figGroups)
    setSingleFigures(singles)
    setParsedFigures(parsedFigures)

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
  }, [content, figures])

  // Render the content with figures
  const renderContent = () => {
    if (!processedContent) return null

    // Split by figure placeholders
    const segments = processedContent.split(/\[FIGURE_PLACEHOLDER_(\d+)\]/)
    const result = []

    for (let i = 0; i < segments.length; i++) {
      // Add the text part
      if (segments[i]) {
        result.push(
          <div key={`text-${i}`} dangerouslySetInnerHTML={{ __html: segments[i] }} className="academic-text" />
        )
      }

      // Check if there's a figure placeholder to replace
      if (i + 1 < segments.length && !isNaN(Number(segments[i + 1]))) {
        const figureIndex = parseInt(segments[i + 1])
        
        // Get the figure from the original parsedFigures array
        const figure = parsedFigures?.[figureIndex]
        
        if (figure) {
          // Check if this figure is part of a subfigure group with multiple figures
          if (figure.baseNumber && figure.subIndex) {
            const group = figureGroups.find(g => 
              g.baseNumber === figure.baseNumber
            )
            
            // If there's a group and this is the first subfigure in that group we've encountered
            if (group && group.placeholder === `[FIGURE_PLACEHOLDER_${figureIndex}]`) {
              // Render the whole group as a SubfigureGroup component
              result.push(
                <SubfigureGroup
                  key={`group-${group.baseNumber}-${figureIndex}`}
                  subfigures={group.figures.map((fig) => ({
                    src: fig.src,
                    alt: fig.alt,
                    index: fig.subIndex || "",
                    caption: fig.caption,
                    parent_caption: fig.parent_caption || group.caption
                  }))}
                  groupTitle={group.title}
                  caption={group.caption}
                  className="my-6"
                />
              )
            } else {
              // This is either a lone subfigure or a subfigure that's part of a group
              // but not the first one we've encountered. Render it individually.
              const displayAlt = `Figure ${figure.baseNumber}${figure.subIndex ? `.${figure.subIndex}` : ''}`
              result.push(
                <ExpandableFigure 
                  key={`figure-${figureIndex}`} 
                  src={figure.src} 
                  alt={displayAlt} 
                  caption={figure.caption || figure.parent_caption}
                  className="my-5" 
                />
              )
            }
          } else {
            // This is a regular figure, not part of a subfigure group
            const displayAlt = figure.baseNumber 
              ? `Figure ${figure.baseNumber}` 
              : figure.alt
            
            result.push(
              <ExpandableFigure 
                key={`figure-${figureIndex}`} 
                src={figure.src} 
                alt={displayAlt} 
                caption={figure.caption}
                className="my-5" 
              />
            )
          }
        }
        i++ // Skip the figure index part
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
      {renderContent()}
    </div>
  )
}