"use client"

import React from "react"

interface EnhancedMarkdownProps {
  content: string
  className?: string
}

export default function EnhancedMarkdown({ content, className = "" }: EnhancedMarkdownProps) {
  // Process the markdown content
  const processedContent = React.useMemo(() => {
    if (!content) return []

    // Split the content into blocks (paragraphs, headings, images, etc.)
    const blocks = content.split("\n\n").filter((block) => block.trim() !== "")

    return blocks.map((block, index) => {
      // Process headings
      if (block.startsWith("# ")) {
        return {
          type: "h1",
          content: block.substring(2),
          key: `h1-${index}`,
        }
      }

      if (block.startsWith("## ")) {
        return {
          type: "h2",
          content: block.substring(3),
          key: `h2-${index}`,
        }
      }

      if (block.startsWith("### ")) {
        return {
          type: "h3",
          content: block.substring(4),
          key: `h3-${index}`,
        }
      }

      // Process images
      const imageRegex = /!\[(.*?)\]$$(.*?)$$/g
      const imageMatches = [...block.matchAll(imageRegex)]

      if (imageMatches.length > 0) {
        // If the block only contains an image
        if (imageMatches[0][0] === block.trim()) {
          return {
            type: "image",
            alt: imageMatches[0][1],
            src: imageMatches[0][2],
            key: `img-${index}`,
          }
        }

        // If the block contains text and images
        const processedBlock = block
        const elements = []

        // Extract any text before the first image
        const textBeforeImage = block.substring(0, block.indexOf("!["))
        if (textBeforeImage.trim()) {
          elements.push({
            type: "p",
            content: textBeforeImage.trim(),
            key: `p-before-img-${index}`,
          })
        }

        // Process all images
        imageMatches.forEach((match, i) => {
          elements.push({
            type: "image",
            alt: match[1],
            src: match[2],
            key: `img-${index}-${i}`,
          })

          // Extract text between images if any
          const currentMatchEnd = match.index! + match[0].length
          const nextMatchStart = i < imageMatches.length - 1 ? imageMatches[i + 1].index : block.length

          const textBetween = block.substring(currentMatchEnd, nextMatchStart)
          if (textBetween.trim()) {
            elements.push({
              type: "p",
              content: textBetween.trim(),
              key: `p-between-img-${index}-${i}`,
            })
          }
        })

        return {
          type: "complex",
          elements,
          key: `complex-${index}`,
        }
      }

      // Process lists
      if (block.includes("\n- ") || block.startsWith("- ")) {
        const items = block.split("\n- ")
        const listItems = []

        // If the block starts with a list item
        if (block.startsWith("- ")) {
          items.forEach((item, i) => {
            if (i === 0) {
              listItems.push(item.substring(2))
            } else {
              listItems.push(item)
            }
          })
        } else {
          // If the block has text before the list
          const textBeforeList = items[0]
          if (textBeforeList.trim()) {
            listItems.push({
              type: "p",
              content: textBeforeList.trim(),
              key: `p-before-list-${index}`,
            })
          }

          // Add list items
          for (let i = 1; i < items.length; i++) {
            listItems.push(items[i])
          }
        }

        return {
          type: "list",
          items: listItems,
          key: `list-${index}`,
        }
      }

      // Process bold text
      const hasBoldText = block.includes("**")
      if (hasBoldText) {
        const parts = []
        const currentText = block
        let boldMatch

        // Regular expression to match bold text
        const boldRegex = /\*\*(.*?)\*\*/g

        let lastIndex = 0
        while ((boldMatch = boldRegex.exec(currentText)) !== null) {
          // Add text before the bold part
          if (boldMatch.index > lastIndex) {
            parts.push({
              type: "text",
              content: currentText.substring(lastIndex, boldMatch.index),
              key: `text-${index}-${lastIndex}`,
            })
          }

          // Add the bold part
          parts.push({
            type: "bold",
            content: boldMatch[1],
            key: `bold-${index}-${boldMatch.index}`,
          })

          lastIndex = boldMatch.index + boldMatch[0].length
        }

        // Add any remaining text
        if (lastIndex < currentText.length) {
          parts.push({
            type: "text",
            content: currentText.substring(lastIndex),
            key: `text-${index}-${lastIndex}`,
          })
        }

        return {
          type: "formatted-p",
          parts,
          key: `formatted-p-${index}`,
        }
      }

      // Default to paragraph
      return {
        type: "p",
        content: block,
        key: `p-${index}`,
      }
    })
  }, [content])

  // Render the processed content
  const renderContent = () => {
    return processedContent.map((block) => {
      switch (block.type) {
        case "h1":
          return (
            <h1 key={block.key} className="text-2xl font-bold mt-6 mb-4">
              {block.content}
            </h1>
          )
        case "h2":
          return (
            <h2 key={block.key} className="text-xl font-bold mt-5 mb-3">
              {block.content}
            </h2>
          )
        case "h3":
          return (
            <h3 key={block.key} className="text-lg font-bold mt-4 mb-2">
              {block.content}
            </h3>
          )
        case "image":
          return (
            <div key={block.key} className="my-6">
              <img
                src={block.src || "/placeholder.svg"}
                alt={block.alt || "Figure"}
                className="max-w-full h-auto rounded-md mx-auto"
              />
              {block.alt && <p className="text-center text-sm text-gray-600 mt-2 italic">{block.alt}</p>}
            </div>
          )
        case "complex":
          return (
            <div key={block.key}>
              {block.elements.map((element) => {
                if (element.type === "p") {
                  return (
                    <p key={element.key} className="mb-4">
                      {element.content}
                    </p>
                  )
                }
                if (element.type === "image") {
                  return (
                    <div key={element.key} className="my-6">
                      <img
                        src={element.src || "/placeholder.svg"}
                        alt={element.alt || "Figure"}
                        className="max-w-full h-auto rounded-md mx-auto"
                      />
                      {element.alt && <p className="text-center text-sm text-gray-600 mt-2 italic">{element.alt}</p>}
                    </div>
                  )
                }
                return null
              })}
            </div>
          )
        case "list":
          return (
            <div key={block.key}>
              {typeof block.items[0] === "object" && block.items[0].type === "p" && (
                <p className="mb-4">{block.items[0].content}</p>
              )}
              <ul className="list-disc pl-6 mb-4">
                {block.items
                  .filter((item) => typeof item === "string")
                  .map((item, i) => (
                    <li key={`${block.key}-item-${i}`} className="mb-1">
                      {item}
                    </li>
                  ))}
              </ul>
            </div>
          )
        case "formatted-p":
          return (
            <p key={block.key} className="mb-4">
              {block.parts.map((part) => {
                if (part.type === "bold") {
                  return <strong key={part.key}>{part.content}</strong>
                }
                return <span key={part.key}>{part.content}</span>
              })}
            </p>
          )
        case "p":
        default:
          return (
            <p key={block.key} className="mb-4">
              {block.content}
            </p>
          )
      }
    })
  }

  return <div className={`markdown-content ${className}`}>{renderContent()}</div>
}

