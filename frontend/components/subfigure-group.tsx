"use client"

import { useState } from "react"
import FigureModal from "./figure-modal"
import { marked } from "marked"
import DOMPurify from "dompurify"
import katex from "katex"
import "katex/dist/katex.min.css"

interface Subfigure {
  src: string
  alt: string
  index: string | number
  caption?: string
  parent_caption?: string
}

interface SubfigureGroupProps {
  subfigures: Subfigure[]
  groupTitle: string
  className?: string
  caption?: string
}

export default function SubfigureGroup({ subfigures, groupTitle, className = "", caption }: SubfigureGroupProps) {
  const [selectedFigure, setSelectedFigure] = useState<Subfigure | null>(null)
  const [showAllFigures, setShowAllFigures] = useState(false)
  const [hoverGroup, setHoverGroup] = useState(false)

  if (!subfigures.length) return null

  // Check if we have a parent_caption from the subfigures
  // First try to get parent_caption from the first subfigure that has one
  let parentCaption = subfigures.find(fig => fig.parent_caption)?.parent_caption || caption;
  
  // If we still don't have a parent caption and we have a caption prop, use that
  if (!parentCaption && caption) {
    parentCaption = caption;
  }

  // Extract figure number from groupTitle
  const figureNumber = groupTitle.replace(/[^\d]/g, '');

  // Display the parent caption with some debugging info if not shown
  {console.log("SubfigureGroup parentCaption", parentCaption, "subfigures[0].parent_caption", subfigures[0]?.parent_caption)}

  // Function to handle expanding all subfigures
  const handleExpandAll = (e: React.MouseEvent) => {
    // Only trigger if clicking the container directly, not its children
    if (e.currentTarget === e.target) {
      setShowAllFigures(true);
      e.stopPropagation();
    }
  };
  
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
        .neon-glow-group:hover {
          box-shadow: 0 0 12px 2px rgba(66, 153, 225, 0.5), 0 0 18px 5px rgba(99, 102, 241, 0.3);
          transition: box-shadow 0.3s ease;
        }
        .neon-glow-item:hover {
          box-shadow: 0 0 8px 1px rgba(66, 153, 225, 0.5), 0 0 12px 3px rgba(99, 102, 241, 0.3);
          transition: box-shadow 0.3s ease;
        }
        .subfigure-container {
          max-height: 350px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .subfigure-container img {
          max-height: 300px;
          object-fit: contain;
        }
      `}</style>
      <div 
        className={`bg-white border border-gray-200 rounded-md transition-all duration-300 p-4 mb-6 ${className} cursor-pointer neon-glow-group`}
        onMouseEnter={() => setHoverGroup(true)}
        onMouseLeave={() => setHoverGroup(false)}
        onClick={handleExpandAll}
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 mb-4">
          {subfigures.map((subfigure) => (
            <div 
              key={subfigure.index} 
              className="relative group bg-white border border-gray-100 rounded-sm p-3 transition-all duration-300 neon-glow-item"
              onClick={(e) => {
                e.stopPropagation();
                setSelectedFigure(subfigure);
              }}
            >
              <div className="overflow-hidden transition-all duration-300 subfigure-container">
                <img
                  src={subfigure.src || "/placeholder.svg"}
                  alt={subfigure.alt}
                  className={`max-w-full transition-all duration-300 transform ${
                    hoverGroup ? "scale-102" : ""
                  }`}
                />
              </div>

              <div className={`text-sm text-gray-700 mt-3 font-serif ${!subfigure.caption ? "text-center" : ""}`}>
                {subfigure.caption ? (
                  <div>
                    <b>{subfigure.alt}:</b>{" "}
                    <span dangerouslySetInnerHTML={{ __html: renderMarkdown(subfigure.caption) }} />
                  </div>
                ) : (
                  <p><b>{subfigure.alt}</b></p>
                )}
              </div>
            </div>
          ))}
        </div>
        
        {/* Caption below subfigures */}
        {parentCaption && (
          <p className="text-sm text-gray-700 mt-3 font-serif">
            <b>Figure {figureNumber}:</b>{" "}
            <span dangerouslySetInnerHTML={{ __html: renderMarkdown(parentCaption) }} />
          </p>
        )}
        {!parentCaption && subfigures[0]?.parent_caption && (
          <p className="text-sm text-gray-700 mt-3 font-serif text-red-500">
            DEBUG: Parent caption exists but not showing: {subfigures[0].parent_caption}
          </p>
        )}
      </div>

      {/* Modal for individual subfigure */}
      {selectedFigure && (
        <FigureModal
          isOpen={!!selectedFigure}
          onClose={() => setSelectedFigure(null)}
          src={selectedFigure.src}
          alt={selectedFigure.alt}
          caption={selectedFigure.caption || selectedFigure.parent_caption}
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
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 overflow-auto max-h-[80vh] p-4">
              {subfigures.map((subfigure) => (
                <div key={`modal-${subfigure.index}`} className="bg-white rounded-md overflow-hidden">
                  <img 
                    src={subfigure.src || "/placeholder.svg"} 
                    alt={subfigure.alt} 
                    className="w-full h-auto object-contain"
                  />
                  <div className={`text-sm text-gray-700 mt-3 font-serif p-2 ${!subfigure.caption ? "text-center" : ""}`}>
                    {subfigure.caption ? (
                      <div>
                        <b>{subfigure.alt}:</b>{" "}
                        <span dangerouslySetInnerHTML={{ __html: renderMarkdown(subfigure.caption) }} />
                      </div>
                    ) : (
                      <p><b>{subfigure.alt}</b></p>
                    )}
                  </div>
                </div>
              ))}
            </div>
            
            {/* Caption below subfigures in modal */}
            {parentCaption && (
              <p className="text-sm text-gray-700 mt-6 font-serif">
                <b>Figure {figureNumber}:</b>{" "}
                <span dangerouslySetInnerHTML={{ __html: renderMarkdown(parentCaption) }} />
              </p>
            )}
            {!parentCaption && subfigures[0]?.parent_caption && (
              <p className="text-sm text-gray-700 mt-6 font-serif text-red-500">
                DEBUG: Parent caption exists but not showing: {subfigures[0].parent_caption}
              </p>
            )}
          </div>
        </div>
      )}
    </>
  )
}

