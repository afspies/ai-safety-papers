"use client"

import { useState } from "react"
import FigureModal from "./figure-modal"

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
  const [showAllFigures, setShowAllFigures] = useState(false)
  const [hoverGroup, setHoverGroup] = useState(false)

  if (!subfigures.length) return null

  // Function to handle expanding all subfigures
  const handleExpandAll = (e: React.MouseEvent) => {
    // Only trigger if clicking the container directly, not its children
    if (e.currentTarget === e.target) {
      setShowAllFigures(true);
      e.stopPropagation();
    }
  };

  return (
    <>
      <style jsx>{`
        .neon-glow-group:hover {
          box-shadow: 0 0 12px 2px rgba(66, 153, 225, 0.5), 0 0 18px 5px rgba(99, 102, 241, 0.3);
          transition: box-shadow 0.3s ease;
        }
        .neon-glow-item:hover {
          box-shadow: 0 0 8px 1px rgba(66, 153, 225, 0.5), 0 0 12px 3px rgba(99, 102, 241, 0.3);
          transition: box-shadow 0.3s ease;
        }
      `}</style>
      <div 
        className={`bg-white border border-gray-200 rounded-md transition-all duration-300 p-4 mb-6 ${className} cursor-pointer neon-glow-group`}
        onMouseEnter={() => setHoverGroup(true)}
        onMouseLeave={() => setHoverGroup(false)}
        onClick={handleExpandAll}
      >
        <h4 className="text-base font-semibold mb-4 font-serif text-center">{groupTitle}</h4>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {subfigures.map((subfigure) => (
            <div 
              key={subfigure.index} 
              className="relative group bg-white border border-gray-100 rounded-sm p-3 transition-all duration-300 neon-glow-item"
              onClick={(e) => {
                e.stopPropagation();
                setSelectedFigure(subfigure);
              }}
            >
              <div className="overflow-hidden transition-all duration-300">
                <img
                  src={subfigure.src || "/placeholder.svg"}
                  alt={subfigure.alt}
                  className={`max-w-full h-auto transition-all duration-300 transform ${
                    hoverGroup ? "scale-102" : ""
                  }`}
                />
              </div>

              <p className="text-center text-sm text-gray-700 mt-3 font-serif">{subfigure.alt}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Modal for individual subfigure */}
      {selectedFigure && (
        <FigureModal
          isOpen={!!selectedFigure}
          onClose={() => setSelectedFigure(null)}
          src={selectedFigure.src}
          alt={selectedFigure.alt}
        />
      )}

      {/* Modal for all subfigures */}
      {showAllFigures && (
        <div 
          className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4 transition-opacity duration-300"
          onClick={() => setShowAllFigures(false)}
        >
          <div 
            className="relative max-w-6xl max-h-[90vh] bg-white rounded-lg shadow-xl overflow-hidden p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="absolute top-3 right-3 p-2 rounded-full bg-white/80 hover:bg-white text-gray-800 z-10 transition-all"
              onClick={() => setShowAllFigures(false)}
              aria-label="Close"
            >
              X
            </button>

            <h3 className="text-lg font-semibold mb-6 text-center">{groupTitle}</h3>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 overflow-auto max-h-[80vh] p-4">
              {subfigures.map((subfigure) => (
                <div key={`modal-${subfigure.index}`} className="bg-white rounded-md overflow-hidden">
                  <img 
                    src={subfigure.src || "/placeholder.svg"} 
                    alt={subfigure.alt} 
                    className="w-full h-auto object-contain"
                  />
                  <p className="text-center text-sm text-gray-700 mt-3 font-serif p-2">{subfigure.alt}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  )
}

