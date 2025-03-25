"use client"

import { MDXRemote } from "next-mdx-remote/rsc"
import remarkGfm from "remark-gfm"

interface MDXContentProps {
  content: string
}

export default function MDXContent({ content }: MDXContentProps) {
  return (
    <div className="markdown-content">
      <MDXRemote
        source={content}
        options={{
          mdxOptions: {
            remarkPlugins: [remarkGfm],
            format: "mdx",
          },
        }}
      />
    </div>
  )
}

