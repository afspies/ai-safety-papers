"use client"

interface SimpleMarkdownProps {
  content: string
  className?: string
}

export default function SimpleMarkdown({ content, className = "" }: SimpleMarkdownProps) {
  // Function to convert markdown to HTML (very basic implementation)
  const renderMarkdown = (text: string) => {
    // Split by paragraphs
    const paragraphs = text.split("\n\n")

    return (
      <>
        {paragraphs.map((paragraph, index) => {
          // Check if it's a heading
          if (paragraph.startsWith("# ")) {
            return (
              <h1 key={index} className="text-2xl font-bold mt-6 mb-4">
                {paragraph.substring(2)}
              </h1>
            )
          }
          if (paragraph.startsWith("## ")) {
            return (
              <h2 key={index} className="text-xl font-bold mt-5 mb-3">
                {paragraph.substring(3)}
              </h2>
            )
          }
          if (paragraph.startsWith("### ")) {
            return (
              <h3 key={index} className="text-lg font-bold mt-4 mb-2">
                {paragraph.substring(4)}
              </h3>
            )
          }

          // Check if it's a list
          if (paragraph.includes("\n- ")) {
            const listItems = paragraph.split("\n- ")
            return (
              <ul key={index} className="list-disc pl-6 mb-4">
                {listItems.map((item, i) => {
                  if (i === 0 && !paragraph.startsWith("- ")) {
                    return (
                      <p key={`p-${i}`} className="mb-2">
                        {item}
                      </p>
                    )
                  }
                  const content = i === 0 && paragraph.startsWith("- ") ? item.substring(2) : item
                  return content ? (
                    <li key={`li-${i}`} className="mb-1">
                      {content}
                    </li>
                  ) : null
                })}
              </ul>
            )
          }

          // Check if it's a numbered list
          if (paragraph.includes("\n1. ") || paragraph.startsWith("1. ")) {
            const listItems = paragraph.startsWith("1. ") ? paragraph.split("\n") : paragraph.split("\n1. ")

            return (
              <ol key={index} className="list-decimal pl-6 mb-4">
                {listItems.map((item, i) => {
                  if (i === 0 && !paragraph.startsWith("1. ")) {
                    return (
                      <p key={`p-${i}`} className="mb-2">
                        {item}
                      </p>
                    )
                  }

                  // Remove the number prefix if it exists
                  let content = item
                  if (i === 0 && paragraph.startsWith("1. ")) {
                    content = item.substring(3)
                  } else if (i > 0) {
                    const match = content.match(/^\d+\.\s/)
                    if (match) {
                      content = content.substring(match[0].length)
                    }
                  }

                  return content ? (
                    <li key={`li-${i}`} className="mb-1">
                      {content}
                    </li>
                  ) : null
                })}
              </ol>
            )
          }

          // Regular paragraph
          return (
            <p key={index} className="mb-4">
              {paragraph}
            </p>
          )
        })}
      </>
    )
  }

  return <div className={`markdown-content ${className}`}>{renderMarkdown(content)}</div>
}

