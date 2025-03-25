"use client"

import { useState } from "react"
import FigureModal from "./figure-modal"
import { Maximize2 } from "lucide-react"

interface ExpandableFigureProps {
  src: string
  alt: string
  className?: string
}

export default function ExpandableFigure({ src, alt, className = "" }: ExpandableFigureProps) {
  const [isModalOpen, setIsModalOpen] = useState(false)

  return (
    <>
      <div className={`relative group ${className}`}>
        <img
          src={src || "/placeholder.svg"}
          alt={alt}
          className="max-w-full h-auto rounded-md cursor-pointer hover:opacity-95 transition-opacity"
          onClick={() => setIsModalOpen(true)}
        />

        <button
          className="absolute top-2 right-2 p-1.5 bg-white/80 hover:bg-white rounded-full shadow-sm opacity-0 group-hover:opacity-100 transition-opacity"
          onClick={() => setIsModalOpen(true)}
          aria-label="Expand figure"
        >
          <Maximize2 className="h-4 w-4 text-gray-700" />
        </button>

        {alt && <p className="text-center text-sm text-gray-600 mt-2 italic">{alt}</p>}
      </div>

      <FigureModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} src={src} alt={alt} />
    </>
  )
}

