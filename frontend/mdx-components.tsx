import type { MDXComponents } from "mdx/types"

export function useMDXComponents(components: MDXComponents): MDXComponents {
  return {
    // Customize the base components
    h1: ({ children }) => <h1 className="text-2xl font-bold mt-6 mb-4 font-heading">{children}</h1>,
    h2: ({ children }) => <h2 className="text-xl font-bold mt-5 mb-3 font-heading">{children}</h2>,
    h3: ({ children }) => <h3 className="text-lg font-bold mt-4 mb-2 font-heading">{children}</h3>,
    p: ({ children }) => <p className="mb-4">{children}</p>,
    ul: ({ children }) => <ul className="list-disc pl-6 mb-4">{children}</ul>,
    ol: ({ children }) => <ol className="list-decimal pl-6 mb-4">{children}</ol>,
    li: ({ children }) => <li className="mb-1">{children}</li>,
    blockquote: ({ children }) => (
      <blockquote className="border-l-4 border-gray-300 pl-4 italic my-4">{children}</blockquote>
    ),
    a: ({ href, children }) => (
      <a href={href} className="text-blue-600 hover:text-blue-800 underline">
        {children}
      </a>
    ),
    img: ({ src, alt }) => {
      if (!src) return null

      return (
        <div className="my-6">
          <img src={src || "/placeholder.svg"} alt={alt || ""} className="max-w-full h-auto rounded-md mx-auto" />
          {alt && <p className="text-center text-sm text-gray-600 mt-2 italic">{alt}</p>}
        </div>
      )
    },
    ...components,
  }
}

