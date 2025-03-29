"use client"

import { useState } from "react"
import Image from "next/image"
import FigureModal from "./figure-modal"
import { Maximize2 } from "lucide-react"

interface ExpandableImageProps {
  src: string
  alt: string
  className?: string
  width?: number
  height?: number
  caption?: string
}

export default function ExpandableImage({ src, alt, className = "", width, height, caption }: ExpandableImageProps) {
  const [isModalOpen, setIsModalOpen] = useState(false)

  return (
    <>
      <div className={`relative group ${className}`}>
        <div className="relative w-full h-48 cursor-pointer" onClick={() => setIsModalOpen(true)}>
          <Image
            src={src || "/placeholder.svg"}
            alt={alt}
            fill
            className="object-contain hover:opacity-95 transition-opacity"
          />

          <button
            className="absolute top-2 right-2 p-1.5 bg-white/80 hover:bg-white rounded-full shadow-sm opacity-0 group-hover:opacity-100 transition-opacity"
            onClick={() => setIsModalOpen(true)}
            aria-label="Expand figure"
          >
            <Maximize2 className="h-4 w-4 text-gray-700" />
          </button>
        </div>
      </div>

      <FigureModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} src={src} alt={alt} caption={caption} />
    </>
  )
}

