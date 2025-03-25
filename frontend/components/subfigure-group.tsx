"use client"

import { useState } from "react"
import FigureModal from "./figure-modal"
import { Maximize2 } from "lucide-react"

interface Subfigure {
  src: string
  alt: string
  index: string | number
}

interface SubfigureGroupProps {
  subfigures: Subfigure[]
  groupTitle: string
  className?: string
}

export default function SubfigureGroup({ subfigures, groupTitle, className = "" }: SubfigureGroupProps) {
  const [selectedFigure, setSelectedFigure] = useState<Subfigure | null>(null)

  if (!subfigures.length) return null

  return (
    <>
      <div className={`mb-8 ${className}`}>
        <h4 className="text-base font-semibold mb-3">{groupTitle}</h4>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {subfigures.map((subfigure) => (
            <div key={subfigure.index} className="relative group">
              <img
                src={subfigure.src || "/placeholder.svg"}
                alt={subfigure.alt}
                className="max-w-full h-auto rounded-md cursor-pointer hover:opacity-95 transition-opacity"
                onClick={() => setSelectedFigure(subfigure)}
              />

              <button
                className="absolute top-2 right-2 p-1.5 bg-white/80 hover:bg-white rounded-full shadow-sm opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={() => setSelectedFigure(subfigure)}
                aria-label={`Expand ${subfigure.alt}`}
              >
                <Maximize2 className="h-4 w-4 text-gray-700" />
              </button>

              <p className="text-center text-sm text-gray-600 mt-2 italic">{subfigure.alt}</p>
            </div>
          ))}
        </div>
      </div>

      {selectedFigure && (
        <FigureModal
          isOpen={!!selectedFigure}
          onClose={() => setSelectedFigure(null)}
          src={selectedFigure.src}
          alt={selectedFigure.alt}
        />
      )}
    </>
  )
}

