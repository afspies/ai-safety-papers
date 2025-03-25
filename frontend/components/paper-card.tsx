"use client"

import type { PaperSummary } from "@/lib/types"
import Link from "next/link"
import { useState, useEffect } from "react"
import Image from "next/image"

interface PaperCardProps {
  paper: PaperSummary
}

export default function PaperCard({ paper }: PaperCardProps) {
  const [isHovered, setIsHovered] = useState(false)
  const [isMounted, setIsMounted] = useState(false)

  useEffect(() => {
    setIsMounted(true)
  }, [])

  if (!isMounted) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden h-full">
        <div className="relative h-48 w-full bg-gray-50 flex items-center justify-center">
          <Image
            src={paper.thumbnail_url || "/placeholder.svg"}
            alt={paper.title}
            fill
            className="object-contain p-2"
          />
        </div>
        <div className="p-4">
          <h3 className="text-lg font-heading font-semibold line-clamp-2">{paper.title}</h3>
          <p className="text-sm text-gray-600 mt-1 line-clamp-1">{paper.authors.join(", ")}</p>
          {paper.highlight && (
            <span className="inline-block bg-yellow-50 text-yellow-800 text-xs px-2 py-1 rounded mt-2 font-medium">
              Highlighted
            </span>
          )}
        </div>
      </div>
    )
  }

  return (
    <Link href={`/paper/${paper.uid}`}>
      <div
        className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden h-full transition-transform duration-200 hover:shadow-md hover:-translate-y-1"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <div className="relative h-48 w-full bg-gray-50 flex items-center justify-center">
          {!isHovered ? (
            <Image
              src={paper.thumbnail_url || "/placeholder.svg"}
              alt={paper.title}
              fill
              className="object-contain p-2"
            />
          ) : (
            <div className="absolute inset-0 bg-gray-800 text-white p-4 overflow-y-auto">
              <p className="text-sm">{paper.tldr}</p>
            </div>
          )}
        </div>
        <div className="p-4">
          <h3 className="text-lg font-heading font-semibold line-clamp-2">{paper.title}</h3>
          <p className="text-sm text-gray-600 mt-1 line-clamp-1">{paper.authors.join(", ")}</p>
          {paper.highlight && (
            <span className="inline-block bg-yellow-50 text-yellow-800 text-xs px-2 py-1 rounded mt-2 font-medium">
              Highlighted
            </span>
          )}
        </div>
      </div>
    </Link>
  )
}

