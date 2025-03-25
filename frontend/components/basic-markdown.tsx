"use client"

interface BasicMarkdownProps {
  content: string
  className?: string
}

export default function BasicMarkdown({ content, className = "" }: BasicMarkdownProps) {
  // Split the content by paragraphs and render each one
  const paragraphs = content.split("\n\n")

  return (
    <div className={`markdown-content ${className}`}>
      {paragraphs.map((paragraph, index) => (
        <p key={index} className="mb-4">
          {paragraph}
        </p>
      ))}
    </div>
  )
}

