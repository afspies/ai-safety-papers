"use client"

import { useEffect, useState } from "react"
import { X } from "lucide-react"

interface FigureModalProps {
  isOpen: boolean
  onClose: () => void
  src: string
  alt: string
}

export default function FigureModal({ isOpen, onClose, src, alt }: FigureModalProps) {
  const [mounted, setMounted] = useState(false)
  const [isAnimating, setIsAnimating] = useState(false)

  // Handle escape key press and animation
  useEffect(() => {
    setMounted(true)

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose()
    }

    if (isOpen) {
      document.addEventListener("keydown", handleEscape)
      // Prevent scrolling when modal is open
      document.body.style.overflow = "hidden"
      // Start animation
      setIsAnimating(true)
    } else {
      setIsAnimating(false)
    }

    return () => {
      document.removeEventListener("keydown", handleEscape)
      document.body.style.overflow = "auto"
    }
  }, [isOpen, onClose])

  if (!mounted) return null

  if (!isOpen && !isAnimating) return null

  return (
    <div 
      className={`fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-8 transition-opacity duration-300 ease-in-out ${
        isOpen ? "opacity-100" : "opacity-0 pointer-events-none"
      }`} 
      onClick={onClose}
      onTransitionEnd={() => {
        if (!isOpen) setIsAnimating(false)
      }}
    >
      <div
        className={`relative max-w-4xl max-h-[90vh] bg-white rounded-xl shadow-xl overflow-hidden transition-transform duration-300 ${
          isOpen ? "scale-100" : "scale-95"
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        <button
          className="absolute top-4 right-4 p-2 rounded-full bg-white/90 hover:bg-white text-gray-800 z-10 transition-all hover:shadow-md"
          onClick={onClose}
          aria-label="Close modal"
        >
          <X className="h-6 w-6" />
        </button>

        <div className="overflow-auto max-h-[90vh] p-6">
          <div className="bg-white p-2 rounded-lg">
            <img src={src || "/placeholder.svg"} alt={alt} className="w-full h-auto object-contain rounded-md" />
          </div>

          {alt && (
            <div className="p-4 bg-white mt-2">
              <p className="text-sm text-gray-700 text-center font-serif">{alt}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

