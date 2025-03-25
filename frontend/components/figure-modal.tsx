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

  // Handle escape key press
  useEffect(() => {
    setMounted(true)

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose()
    }

    if (isOpen) {
      document.addEventListener("keydown", handleEscape)
      // Prevent scrolling when modal is open
      document.body.style.overflow = "hidden"
    }

    return () => {
      document.removeEventListener("keydown", handleEscape)
      document.body.style.overflow = "auto"
    }
  }, [isOpen, onClose])

  if (!mounted) return null

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="relative max-w-4xl max-h-[90vh] bg-white rounded-lg shadow-xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          className="absolute top-2 right-2 p-1 rounded-full bg-white/80 hover:bg-white text-gray-800 z-10"
          onClick={onClose}
          aria-label="Close modal"
        >
          <X className="h-6 w-6" />
        </button>

        <div className="overflow-auto max-h-[90vh]">
          <img src={src || "/placeholder.svg"} alt={alt} className="w-full h-auto object-contain" />

          {alt && (
            <div className="p-4 bg-white border-t border-gray-100">
              <p className="text-sm text-gray-700 italic">{alt}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

