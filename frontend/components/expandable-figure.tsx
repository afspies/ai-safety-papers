"use client"

import { useState } from "react"
import FigureModal from "./figure-modal"
import { marked } from "marked"
import DOMPurify from "dompurify"
import katex from "katex"
import "katex/dist/katex.min.css"

interface ExpandableFigureProps {
  src: string
  alt: string
  caption?: string
  className?: string
}

export default function ExpandableFigure({ src, alt, caption, className = "" }: ExpandableFigureProps) {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isHovered, setIsHovered] = useState(false)
  
  // Convert markdown to HTML with LaTeX support
  const renderMarkdown = (text: string) => {
    if (!text) return "";
    
    // Process LaTeX expressions before markdown rendering
    const processedText = text.replace(/\$([^\$]+)\$/g, (match, latex) => {
      try {
        return katex.renderToString(latex, { 
          throwOnError: false,
          output: 'html'
        });
      } catch (e) {
        console.error("KaTeX error:", e);
        return match; // Return the original text if KaTeX fails
      }
    });
    
    const sanitizedHtml = DOMPurify.sanitize(marked.parse(processedText, { async: false }));
    return sanitizedHtml;
  };

  return (
    <>
      <style jsx>{`
        .neon-glow:hover {
          box-shadow: 0 0 10px 2px rgba(66, 153, 225, 0.6), 0 0 15px 5px rgba(99, 102, 241, 0.4);
          transition: box-shadow 0.3s ease;
        }
        .figure-container {
          max-height: 500px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .figure-container img {
          max-height: 450px;
          object-fit: contain;
        }
      `}</style>
      <div 
        className={`relative group bg-white border border-gray-200 rounded-md hover:shadow-md transition-all duration-300 p-3 ${className} cursor-pointer flex flex-col items-center neon-glow`}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onClick={() => setIsModalOpen(true)}
      >
        <div className="overflow-hidden transition-all duration-300 flex justify-center w-full figure-container">
          <img
            src={src || "/placeholder.svg"}
            alt={alt}
            className={`max-w-full transition-all duration-300 transform ${
              isHovered ? "scale-102" : ""
            }`}
          />
        </div>

        {(caption || alt) && (
          <div className={`text-sm text-gray-700 mt-3 font-serif w-full ${!caption ? "text-center" : ""}`}>
            {caption ? (
              <div>
                <b>{alt}:</b>{" "}
                <span dangerouslySetInnerHTML={{ __html: renderMarkdown(caption) }} />
              </div>
            ) : (
              <p><b>{alt}</b></p>
            )}
          </div>
        )}
      </div>

      <FigureModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} src={src} alt={alt} caption={caption} />
    </>
  )
}

