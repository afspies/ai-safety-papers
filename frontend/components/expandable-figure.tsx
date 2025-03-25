"use client"

import { useState } from "react"
import FigureModal from "./figure-modal"

interface ExpandableFigureProps {
  src: string
  alt: string
  className?: string
}

export default function ExpandableFigure({ src, alt, className = "" }: ExpandableFigureProps) {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isHovered, setIsHovered] = useState(false)

  return (
    <>
      <style jsx>{`
        .neon-glow:hover {
          box-shadow: 0 0 10px 2px rgba(66, 153, 225, 0.6), 0 0 15px 5px rgba(99, 102, 241, 0.4);
          transition: box-shadow 0.3s ease;
        }
      `}</style>
      <div 
        className={`relative group bg-white border border-gray-200 rounded-md hover:shadow-md transition-all duration-300 p-3 ${className} cursor-pointer flex flex-col items-center neon-glow`}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onClick={() => setIsModalOpen(true)}
      >
        <div className="overflow-hidden transition-all duration-300 flex justify-center w-full">
          <img
            src={src || "/placeholder.svg"}
            alt={alt}
            className={`max-w-full h-auto transition-all duration-300 transform ${
              isHovered ? "scale-102" : ""
            }`}
          />
        </div>

        {alt && <p className="text-center text-sm text-gray-700 mt-3 font-serif w-full">{alt}</p>}
      </div>

      <FigureModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} src={src} alt={alt} />
    </>
  )
}

