"use client"

import React from "react"
import { MDXRemote } from "next-mdx-remote"
import { serialize } from "next-mdx-remote/serialize"
import remarkGfm from "remark-gfm"

interface MDXRemoteContentProps {
  content: string
}

export default function MDXRemoteContent({ content }: MDXRemoteContentProps) {
  const [mdxSource, setMdxSource] = React.useState<any>(null)

  React.useEffect(() => {
    async function prepareMDX() {
      if (!content) return

      try {
        const mdxSource = await serialize(content, {
          mdxOptions: {
            remarkPlugins: [remarkGfm],
            format: "mdx",
          },
        })
        setMdxSource(mdxSource)
      } catch (error) {
        console.error("Error serializing MDX:", error)
      }
    }

    prepareMDX()
  }, [content])

  if (!mdxSource) {
    return <div>Loading content...</div>
  }

  return (
    <div className="markdown-content">
      <MDXRemote {...mdxSource} />
    </div>
  )
}

